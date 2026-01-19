#!/usr/bin/env python3
"""
UVM Generator V2 - LLM-Powered UVM Test Case Generation Pipeline

IMPROVEMENTS OVER V1:
- All names derived from Block YAML (no hardcoded IP-specific values)
- Flexible YAML parsers supporting multiple formats
- Dynamic prompts generated from input data
- Scoreboard generation (Phase A.4)
- Better error handling and logging
- Configurable via settings.yaml and uvc_mapping.yaml

Usage:
    python generate_uvm.py --block <block.yaml> --vplan <vplan.yaml> --output <output_dir>
    
For a new IP:
    1. Create your Block YAML describing the DUT
    2. Create your Vplan YAML with test cases
    3. Copy uvc_mapping_template.yaml and customize for your interfaces
    4. Provide example files for few-shot learning
    5. Run the generator
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.parser import (
    BlockYAMLParser, 
    VplanYAMLParser, 
    ParameterTransformer,
    load_uvc_mapping, 
    load_settings
)
from utils.llm_client import LLMClient, LLMError
from utils.file_utils import (
    FileManager, 
    collect_uvc_info, 
    collect_example_files,
    derive_names_from_block
)
from prompts.ip_infra_prompts import (
    get_env_prompt, 
    get_virtual_sequencer_prompt,
    get_interface_prompt,
    get_package_prompt,
    get_scoreboard_prompt
)
from prompts.test_case_prompts import get_test_prompt, get_vseq_prompt


# Configure logging
def setup_logging(level: str = "INFO", log_file: str = None):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


class UVMGenerator:
    """
    Main UVM Generator class orchestrating the pipeline
    
    V2 Improvements:
    - Names derived from block YAML, not hardcoded
    - Supports arbitrary IP blocks
    - Configurable via YAML files
    """
    
    def __init__(self, 
                 block_yaml_path: str,
                 vplan_yaml_path: str,
                 output_dir: str,
                 example_dir: str = None,
                 uvc_lib_path: str = None,
                 api_key: Optional[str] = None,
                 provider: str = None,
                 model: Optional[str] = None,
                 config_dir: Optional[str] = None,
                 uvc_mapping_path: Optional[str] = None):
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configurations
        config_dir = Path(config_dir) if config_dir else Path(__file__).parent / "config"
        self.settings = load_settings(str(config_dir / "settings.yaml"))
        
        # Load UVC mapping (use provided path or default)
        if uvc_mapping_path and Path(uvc_mapping_path).exists():
            self.uvc_mapping = load_uvc_mapping(uvc_mapping_path)
        elif (config_dir / "uvc_mapping.yaml").exists():
            self.uvc_mapping = load_uvc_mapping(str(config_dir / "uvc_mapping.yaml"))
        else:
            self.logger.warning("No UVC mapping found - using empty mapping")
            self.uvc_mapping = {'uvc_mapping': {}, 'transformations': {}, 'packages': []}
        
        # Initialize parsers
        self.block_parser = BlockYAMLParser(block_yaml_path)
        self.vplan_parser = VplanYAMLParser(vplan_yaml_path)
        
        # Initialize parameter transformer
        self.transformer = ParameterTransformer(
            self.uvc_mapping.get('transformations', {})
        )
        
        # Store raw content for prompts
        self.block_yaml_content = Path(block_yaml_path).read_text(encoding='utf-8')
        
        # Initialize LLM client
        llm_settings = self.settings.get('llm', {})
        provider = provider or llm_settings.get('provider', 'anthropic')
        model = model or llm_settings.get('model')
        self.llm = LLMClient(provider=provider, api_key=api_key, model=model)
        
        # Initialize file manager
        self.file_manager = FileManager(output_dir)
        self.file_manager.setup_directories()
        
        # Load examples for few-shot learning
        if example_dir and Path(example_dir).exists():
            self.examples = collect_example_files(example_dir)
        else:
            self.logger.warning(f"Example directory not found: {example_dir}")
            self.examples = {}
        
        # Collect UVC info
        if uvc_lib_path and Path(uvc_lib_path).exists():
            self.uvc_info = collect_uvc_info(uvc_lib_path)
            self.uvc_info_str = "\n\n".join([f"// {k}\n{v}" for k, v in self.uvc_info.items()])
        else:
            self.uvc_info = {}
            self.uvc_info_str = "// No UVC library info available"
        
        # DYNAMIC NAMING: Derive all names from block YAML
        self.block_name = self.block_parser.get_block_name()
        naming_config = self.settings.get('naming', {})
        self.names = derive_names_from_block(self.block_name, naming_config)
        
        # Extract derived names
        self.env_class_name = self.names['env_class']
        self.vseqr_class_name = self.names['vseqr_class']
        self.interface_name = self.names['interface_name']
        self.package_name = self.names['package_name']
        self.scoreboard_class_name = self.names['scoreboard_class']
        
        # Get clock/reset info
        self.clock = self.block_parser.get_clock()
        self.reset = self.block_parser.get_reset()
        self.model_config = self.block_parser.get_model()
        
        # Track generated files for package
        self.vseq_files: List[str] = []
        self.test_files: List[str] = []
        
        # Store generated content for Phase B
        self.generated_env_content = ""
        self.generated_vseqr_content = ""
        
        self.logger.info(f"Initialized UVM Generator for: {self.block_name}")
        self.logger.info(f"  Environment: {self.env_class_name}")
        self.logger.info(f"  Virtual Sequencer: {self.vseqr_class_name}")
        self.logger.info(f"  Interface: {self.interface_name}")
        self.logger.info(f"  Package: {self.package_name}")
    
    def run_phase_a(self, skip_existing: bool = False) -> tuple:
        """
        Phase A: Generate IP Infrastructure
        - Environment (A.1)
        - Virtual Sequencer (A.2)
        - Interface (A.3)
        - Scoreboard (A.4) - NEW in V2
        """
        print("\n" + "=" * 60)
        print("PHASE A: Generating IP Infrastructure")
        print("=" * 60)
        
        interfaces = self.block_parser.get_interfaces()
        
        # A.1: Generate Environment
        print("\n[A.1] Generating Environment...")
        try:
            env_content = self._generate_env(interfaces)
            env_path = self.file_manager.write_file(
                f"ip_infra/env/{self.env_class_name}.sv",
                env_content,
                skip_if_exists=skip_existing
            )
            self.generated_env_content = env_content
            print(f"  [OK] Created: {env_path.name}")
        except LLMError as e:
            print(f"  [FAIL] Failed to generate environment: {e}")
            raise
        
        # A.2: Generate Virtual Sequencer
        print("\n[A.2] Generating Virtual Sequencer...")
        try:
            vseqr_content = self._generate_virtual_sequencer(interfaces)
            vseqr_path = self.file_manager.write_file(
                f"ip_infra/virtual_sequencer/{self.vseqr_class_name}.sv",
                vseqr_content,
                skip_if_exists=skip_existing
            )
            self.generated_vseqr_content = vseqr_content
            print(f"  [OK] Created: {vseqr_path.name}")
        except LLMError as e:
            print(f"  [FAIL] Failed to generate virtual sequencer: {e}")
            raise
        
        # A.3: Generate Interface
        print("\n[A.3] Generating Interface...")
        try:
            interface_content = self._generate_interface(interfaces)
            interface_path = self.file_manager.write_file(
                f"ip_infra/interface/{self.interface_name}.sv",
                interface_content,
                skip_if_exists=skip_existing
            )
            print(f"  [OK] Created: {interface_path.name}")
        except LLMError as e:
            print(f"  [FAIL] Failed to generate interface: {e}")
            raise
        
        # A.4: Generate Scoreboard (NEW in V2)
        print("\n[A.4] Generating Scoreboard...")
        try:
            scoreboard_content = self._generate_scoreboard(interfaces)
            scoreboard_path = self.file_manager.write_file(
                f"ip_infra/scoreboard/{self.scoreboard_class_name}.sv",
                scoreboard_content,
                skip_if_exists=skip_existing
            )
            print(f"  [OK] Created: {scoreboard_path.name}")
        except LLMError as e:
            print(f"  [FAIL] Failed to generate scoreboard: {e}")
            # Scoreboard is optional - continue
            self.logger.warning(f"Scoreboard generation failed: {e}")
        
        print("\n[OK] Phase A complete!")
        return env_content, vseqr_content
    
    def run_phase_b(self, env_content: str = None, vseqr_content: str = None, 
                    test_ids: Optional[List[str]] = None):
        """
        Phase B: Generate Test Cases
        - Test files (*_test.sv)
        - Virtual Sequence files (*_vseq.sv)
        """
        print("\n" + "=" * 60)
        print("PHASE B: Generating Test Cases")
        print("=" * 60)
        
        # Use stored content if not provided
        env_content = env_content or self.generated_env_content
        vseqr_content = vseqr_content or self.generated_vseqr_content
        
        test_cases = self.vplan_parser.get_test_cases()
        
        # Filter if specific test IDs requested
        if test_ids:
            test_cases = [tc for tc in test_cases 
                         if tc.get('TC_ID', tc.get('tc_id', '')) in test_ids]
        
        if not test_cases:
            print("  No test cases found in vplan!")
            return
        
        total = len(test_cases)
        print(f"\nGenerating {total} test case(s)...")
        
        for i, tc in enumerate(test_cases, 1):
            tc_id = tc.get('TC_ID', tc.get('tc_id', f'unknown_{i}'))
            print(f"\n[{i}/{total}] Generating: {tc_id}")
            
            try:
                # Extract config from test case
                tc_config = self.vplan_parser.extract_config(tc)
                
                # Get active UVCs
                active_uvcs = tc_config.get('active_uvcs', [])
                
                # B.1: Generate test file
                print(f"  Generating _test.sv...")
                test_content = self._generate_test(tc_config, env_content)
                test_path = self.file_manager.write_file(
                    f"tests/tests/{tc_id}_test.sv",
                    test_content
                )
                self.test_files.append(f"{tc_id}_test.sv")
                print(f"  [OK] {tc_id}_test.sv")
                
                # B.2: Generate vseq file
                print(f"  Generating _vseq.sv...")
                vseq_content = self._generate_vseq(tc_config, active_uvcs, vseqr_content)
                vseq_path = self.file_manager.write_file(
                    f"tests/virtual_sequences/{tc_id}_vseq.sv",
                    vseq_content
                )
                self.vseq_files.append(f"{tc_id}_vseq.sv")
                print(f"  [OK] {tc_id}_vseq.sv")
                
            except LLMError as e:
                print(f"  [FAIL] Error generating {tc_id}: {e}")
                self.logger.error(f"Failed to generate test case {tc_id}: {e}")
                continue
            except Exception as e:
                print(f"  [FAIL] Unexpected error for {tc_id}: {e}")
                self.logger.exception(f"Unexpected error for {tc_id}")
                continue
        
        print(f"\n[OK] Phase B complete! Generated {len(self.test_files)} test case(s)")
    
    def run_phase_c(self):
        """
        Phase C: Generate Package & Integration
        - Package file
        """
        print("\n" + "=" * 60)
        print("PHASE C: Generating Package & Integration")
        print("=" * 60)
        
        print("\n[C.1] Generating Package File...")
        try:
            package_content = self._generate_package()
            package_path = self.file_manager.write_file(
                f"ip_infra/pkg/{self.package_name}.sv",
                package_content
            )
            print(f"  [OK] Created: {package_path.name}")
        except LLMError as e:
            print(f"  [FAIL] Failed to generate package: {e}")
            raise
        
        print("\n[OK] Phase C complete!")
    
    # =========================================================================
    # Private generation methods
    # =========================================================================
    
    def _generate_env(self, interfaces: List[Dict]) -> str:
        """Generate environment using LLM"""
        prompt = get_env_prompt(
            block_yaml=self.block_yaml_content,
            interfaces=interfaces,
            uvc_info=self.uvc_info_str,
            example_env=self.examples.get('env', ''),
            env_class_name=self.env_class_name,
            vseqr_class_name=self.vseqr_class_name,
            uvc_mapping=self.uvc_mapping
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_virtual_sequencer(self, interfaces: List[Dict]) -> str:
        """Generate virtual sequencer using LLM"""
        prompt = get_virtual_sequencer_prompt(
            block_yaml=self.block_yaml_content,
            interfaces=interfaces,
            example_vseqr=self.examples.get('vseqr', ''),
            vseqr_class_name=self.vseqr_class_name,
            dut_if_name=self.interface_name,
            uvc_mapping=self.uvc_mapping
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_interface(self, interfaces: List[Dict]) -> str:
        """Generate interface using LLM"""
        prompt = get_interface_prompt(
            block_yaml=self.block_yaml_content,
            interfaces=interfaces,
            example_interface=self.examples.get('interface', ''),
            interface_name=self.interface_name,
            clock_name=self.clock.get('name', 'clk'),
            reset_name=self.reset.get('name', 'resetn')
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_scoreboard(self, interfaces: List[Dict]) -> str:
        """Generate scoreboard using LLM (NEW in V2)"""
        prompt = get_scoreboard_prompt(
            block_yaml=self.block_yaml_content,
            interfaces=interfaces,
            example_scoreboard=self.examples.get('scoreboard', ''),
            scoreboard_class_name=self.scoreboard_class_name,
            env_class_name=self.env_class_name
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_test(self, tc_config: dict, env_content: str) -> str:
        """Generate test file using LLM"""
        prompt = get_test_prompt(
            tc_config=tc_config,
            example_test=self.examples.get('test', ''),
            env_class=self.env_class_name,
            vseqr_class=self.vseqr_class_name,
            dut_if_name=self.interface_name,
            reset_signal=self.reset.get('name', 'resetn')
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_vseq(self, tc_config: dict, active_uvcs: list, vseqr_content: str) -> str:
        """Generate virtual sequence using LLM"""
        prompt = get_vseq_prompt(
            tc_config=tc_config,
            active_uvcs=active_uvcs,
            example_vseq=self.examples.get('vseq', ''),
            vseqr_class=self.vseqr_class_name,
            uvc_mapping=self.uvc_mapping,
            generated_vseqr=vseqr_content,
            model_config=self.model_config
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_package(self) -> str:
        """Generate package file using LLM"""
        uvc_packages = self.uvc_mapping.get('packages', [])
        
        prompt = get_package_prompt(
            block_yaml=self.block_yaml_content,
            example_package=self.examples.get('package', ''),
            package_name=self.package_name,
            vseq_includes=self.vseq_files,
            test_includes=self.test_files,
            env_file=f"{self.env_class_name}.sv",
            vseqr_file=f"{self.vseqr_class_name}.sv",
            scoreboard_file=f"{self.scoreboard_class_name}.sv",
            interface_file=f"{self.interface_name}.sv",
            uvc_packages=uvc_packages
        )
        return self.llm.generate_with_retry(prompt)
    
    def print_summary(self):
        """Print generation summary"""
        print(self.file_manager.generate_summary())
    
    def run_all(self, skip_existing: bool = False, test_ids: List[str] = None):
        """Run complete pipeline"""
        env_content, vseqr_content = self.run_phase_a(skip_existing=skip_existing)
        self.run_phase_b(env_content, vseqr_content, test_ids=test_ids)
        self.run_phase_c()
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='UVM Generator V2 - LLM-Powered Code Generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate everything for a new IP
  python generate_uvm.py --block my_ip/block.yaml --vplan my_ip/vplan.yaml --output ./output

  # Generate only infrastructure (Phase A)
  python generate_uvm.py --block block.yaml --vplan vplan.yaml --output ./output --phase-a-only

  # Generate specific test cases
  python generate_uvm.py --block block.yaml --vplan vplan.yaml --output ./output --test-ids TC_001 TC_002

  # Use custom UVC mapping
  python generate_uvm.py --block block.yaml --vplan vplan.yaml --output ./output --uvc-mapping my_uvc_mapping.yaml
        """
    )
    
    # Required arguments
    parser.add_argument('--block', required=True, help='Path to Block YAML file')
    parser.add_argument('--vplan', required=True, help='Path to Vplan YAML file')
    parser.add_argument('--output', required=True, help='Output directory')
    
    # Optional arguments
    parser.add_argument('--examples', default=None,
                        help='Path to example files directory')
    parser.add_argument('--uvc-lib', default=None,
                        help='Path to UVC library directory')
    parser.add_argument('--uvc-mapping', default=None,
                        help='Path to UVC mapping YAML file')
    parser.add_argument('--config-dir', default=None,
                        help='Path to config directory (default: ./config)')
    parser.add_argument('--api-key', help='LLM API key (or set ANTHROPIC_API_KEY/OPENAI_API_KEY env var)')
    parser.add_argument('--provider', default=None, choices=['anthropic', 'openai'],
                        help='LLM provider (default from settings.yaml)')
    parser.add_argument('--model', help='LLM model name (default from settings.yaml)')
    
    # Phase control
    parser.add_argument('--phase-a-only', action='store_true',
                        help='Only run Phase A (infrastructure generation)')
    parser.add_argument('--phase-b-only', action='store_true',
                        help='Only run Phase B (test case generation)')
    parser.add_argument('--test-ids', nargs='+',
                        help='Specific test case IDs to generate')
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip files that already exist')
    
    # Logging
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    parser.add_argument('--log-file', default=None,
                        help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger('main')
    
    # Validate paths
    if not Path(args.block).exists():
        print(f"Error: Block YAML not found: {args.block}")
        sys.exit(1)
    if not Path(args.vplan).exists():
        print(f"Error: Vplan YAML not found: {args.vplan}")
        sys.exit(1)
    
    # Get API key
    api_key = args.api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: API key required. Set --api-key or ANTHROPIC_API_KEY/OPENAI_API_KEY env var")
        sys.exit(1)
    
    print("=" * 60)
    print("UVM Generator V2 - LLM-Powered Code Generation")
    print("=" * 60)
    print(f"Block YAML: {args.block}")
    print(f"Vplan YAML: {args.vplan}")
    print(f"Output Dir: {args.output}")
    if args.examples:
        print(f"Examples:   {args.examples}")
    if args.uvc_mapping:
        print(f"UVC Map:    {args.uvc_mapping}")
    print("=" * 60)
    
    try:
        # Initialize generator
        generator = UVMGenerator(
            block_yaml_path=args.block,
            vplan_yaml_path=args.vplan,
            output_dir=args.output,
            example_dir=args.examples,
            uvc_lib_path=args.uvc_lib,
            api_key=api_key,
            provider=args.provider,
            model=args.model,
            config_dir=args.config_dir,
            uvc_mapping_path=args.uvc_mapping
        )
        
        env_content = ""
        vseqr_content = ""
        
        # Run phases based on arguments
        if args.phase_b_only:
            # Phase B only - need to read existing infrastructure
            print("Warning: --phase-b-only requires existing infrastructure files")
            generator.run_phase_b(test_ids=args.test_ids)
            generator.run_phase_c()
        elif args.phase_a_only:
            # Phase A only
            generator.run_phase_a(skip_existing=args.skip_existing)
        else:
            # Full pipeline
            generator.run_all(skip_existing=args.skip_existing, test_ids=args.test_ids)
        
        # Print summary
        generator.print_summary()
        
        print("\n==> Generation complete!")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        logger.exception("Generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
