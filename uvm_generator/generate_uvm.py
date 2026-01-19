#!/usr/bin/env python3
"""
UVM Generator - LLM-Powered UVM Test Case Generation Pipeline

This tool generates UVM test environments and test cases from:
- Block YAML: IP/DUT description
- Vplan YAML: Verification plan with test case specifications

Usage:
    python generate_uvm.py --block <block.yaml> --vplan <vplan.yaml> --output <output_dir>
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.parser import BlockYAMLParser, VplanYAMLParser, load_uvc_mapping, load_settings
from utils.llm_client import LLMClient
from utils.file_utils import FileManager, collect_uvc_info, collect_example_files
from prompts.ip_infra_prompts import (
    get_env_prompt, 
    get_virtual_sequencer_prompt,
    get_interface_prompt,
    get_package_prompt
)
from prompts.test_case_prompts import get_test_prompt, get_vseq_prompt


class UVMGenerator:
    """Main UVM Generator class orchestrating the pipeline"""
    
    def __init__(self, 
                 block_yaml_path: str,
                 vplan_yaml_path: str,
                 output_dir: str,
                 example_dir: str,
                 uvc_lib_path: str,
                 api_key: Optional[str] = None,
                 provider: str = "anthropic",
                 model: Optional[str] = None,
                 config_dir: Optional[str] = None):
        
        # Load configurations
        config_dir = config_dir or Path(__file__).parent / "config"
        self.settings = load_settings(str(config_dir / "settings.yaml"))
        self.uvc_mapping = load_uvc_mapping(str(config_dir / "uvc_mapping.yaml"))
        
        # Initialize parsers
        self.block_parser = BlockYAMLParser(block_yaml_path)
        self.vplan_parser = VplanYAMLParser(vplan_yaml_path)
        
        # Store raw content for prompts
        self.block_yaml_content = Path(block_yaml_path).read_text()
        
        # Initialize LLM client
        provider = provider or self.settings['llm']['provider']
        model = model or self.settings['llm']['model']
        self.llm = LLMClient(provider=provider, api_key=api_key, model=model)
        
        # Initialize file manager
        self.file_manager = FileManager(output_dir)
        self.file_manager.setup_directories()
        
        # Load examples for few-shot learning
        self.examples = collect_example_files(example_dir)
        
        # Collect UVC info
        self.uvc_info = collect_uvc_info(uvc_lib_path)
        self.uvc_info_str = "\n\n".join([f"// {k}\n{v}" for k, v in self.uvc_info.items()])
        
        # Derive naming from block
        self.block_name = self.block_parser.get_block_name()
        self.env_class_name = f"p18_{self.block_name.replace('_m', '').replace('dimc_tile_wrapper', 'dimc_tile_wrap')}_env"
        self.vseqr_class_name = f"p18_{self.block_name.replace('_m', '').replace('dimc_tile_wrapper', 'dimc_tile_wrap')}_virtual_sequencer"
        self.interface_name = "dimc_tilewrap_if"
        self.package_name = "dimc_tile_wrap_pkg"
        
        # Track generated files for package
        self.vseq_files: List[str] = []
        self.test_files: List[str] = []
    
    def run_phase_a(self, skip_existing: bool = False):
        """
        Phase A: Generate IP Infrastructure
        - Environment
        - Virtual Sequencer
        - Interface
        """
        print("\n" + "=" * 60)
        print("PHASE A: Generating IP Infrastructure")
        print("=" * 60)
        
        # Generate Environment
        print("\n[1/3] Generating Environment...")
        env_content = self._generate_env()
        env_path = self.file_manager.write_file(
            f"ip_infra/env/{self.env_class_name}.sv",
            env_content
        )
        print(f"  ✓ Created: {env_path.name}")
        
        # Generate Virtual Sequencer
        print("\n[2/3] Generating Virtual Sequencer...")
        vseqr_content = self._generate_virtual_sequencer()
        vseqr_path = self.file_manager.write_file(
            f"ip_infra/virtual_sequencer/{self.vseqr_class_name}.sv",
            vseqr_content
        )
        print(f"  ✓ Created: {vseqr_path.name}")
        
        # Generate Interface
        print("\n[3/3] Generating Interface...")
        interface_content = self._generate_interface()
        interface_path = self.file_manager.write_file(
            f"ip_infra/interface/{self.interface_name}.sv",
            interface_content
        )
        print(f"  ✓ Created: {interface_path.name}")
        
        print("\n✓ Phase A complete!")
        return env_content, vseqr_content
    
    def run_phase_b(self, env_content: str, vseqr_content: str, 
                    test_ids: Optional[List[str]] = None):
        """
        Phase B: Generate Test Cases
        - Test files (*_test.sv)
        - Virtual Sequence files (*_vseq.sv)
        """
        print("\n" + "=" * 60)
        print("PHASE B: Generating Test Cases")
        print("=" * 60)
        
        test_cases = self.vplan_parser.get_test_cases()
        
        # Filter if specific test IDs requested
        if test_ids:
            test_cases = [tc for tc in test_cases if tc.get('TC_ID') in test_ids]
        
        total = len(test_cases)
        print(f"\nGenerating {total} test cases...")
        
        for i, tc in enumerate(test_cases, 1):
            tc_id = tc.get('TC_ID', f'unknown_{i}')
            print(f"\n[{i}/{total}] Generating: {tc_id}")
            
            try:
                # Extract config from test case
                tc_config = self.vplan_parser.extract_config(tc)
                tc_config['mode_int'] = self.vplan_parser.get_mode_int(tc_config['mode'])
                tc_config['sign_int'] = self.vplan_parser.get_sign_int(tc_config['sign_8b'])
                
                # Generate test file
                test_content = self._generate_test(tc_config, env_content)
                test_path = self.file_manager.write_file(
                    f"tests/tests/{tc_id}_test.sv",
                    test_content
                )
                self.test_files.append(f"{tc_id}_test.sv")
                print(f"  ✓ {tc_id}_test.sv")
                
                # Generate vseq file
                vseq_content = self._generate_vseq(tc_config, tc.get('Active_UVCs', []))
                vseq_path = self.file_manager.write_file(
                    f"tests/virtual_sequences/{tc_id}_vseq.sv",
                    vseq_content
                )
                self.vseq_files.append(f"{tc_id}_vseq.sv")
                print(f"  ✓ {tc_id}_vseq.sv")
                
            except Exception as e:
                print(f"  ✗ Error generating {tc_id}: {e}")
                continue
        
        print(f"\n✓ Phase B complete! Generated {len(self.test_files)} test cases")
    
    def generate_package(self):
        """Generate the package file with all includes"""
        print("\n" + "=" * 60)
        print("Generating Package File")
        print("=" * 60)
        
        package_content = self._generate_package()
        package_path = self.file_manager.write_file(
            f"ip_infra/pkg/{self.package_name}.sv",
            package_content
        )
        print(f"  ✓ Created: {package_path.name}")
    
    def _generate_env(self) -> str:
        """Generate environment using LLM"""
        prompt = get_env_prompt(
            block_yaml=self.block_yaml_content,
            uvc_info=self.uvc_info_str,
            example_env=self.examples.get('env', ''),
            env_class_name=self.env_class_name,
            vseqr_class_name=self.vseqr_class_name
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_virtual_sequencer(self) -> str:
        """Generate virtual sequencer using LLM"""
        prompt = get_virtual_sequencer_prompt(
            block_yaml=self.block_yaml_content,
            example_vseqr=self.examples.get('vseqr', ''),
            vseqr_class_name=self.vseqr_class_name,
            dut_if_name=self.interface_name
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_interface(self) -> str:
        """Generate interface using LLM"""
        clock = self.block_parser.get_clock()
        reset = self.block_parser.get_reset()
        
        prompt = get_interface_prompt(
            block_yaml=self.block_yaml_content,
            example_interface=self.examples.get('interface', ''),
            interface_name=self.interface_name,
            clock_name=clock.get('name', 'clk'),
            reset_name=reset.get('name', 'resetn')
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_test(self, tc_config: dict, env_content: str) -> str:
        """Generate test file using LLM"""
        prompt = get_test_prompt(
            tc_config=tc_config,
            example_test=self.examples.get('test', ''),
            env_class=self.env_class_name,
            vseqr_class=self.vseqr_class_name,
            dut_if_name=self.interface_name
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_vseq(self, tc_config: dict, active_uvcs: list) -> str:
        """Generate virtual sequence using LLM"""
        prompt = get_vseq_prompt(
            tc_config=tc_config,
            example_vseq=self.examples.get('vseq', ''),
            vseqr_class=self.vseqr_class_name,
            active_uvcs=active_uvcs,
            uvc_mapping=self.uvc_mapping
        )
        return self.llm.generate_with_retry(prompt)
    
    def _generate_package(self) -> str:
        """Generate package file using LLM"""
        prompt = get_package_prompt(
            block_yaml=self.block_yaml_content,
            example_package=self.examples.get('package', ''),
            package_name=self.package_name,
            vseq_includes=self.vseq_files,
            test_includes=self.test_files,
            env_file=f"{self.env_class_name}.sv",
            vseqr_file=f"{self.vseqr_class_name}.sv",
            scoreboard_file=f"p18_dimc_tile_wrap_scoreboard.sv"
        )
        return self.llm.generate_with_retry(prompt)
    
    def print_summary(self):
        """Print generation summary"""
        print(self.file_manager.generate_summary())


def main():
    parser = argparse.ArgumentParser(
        description='LLM-Powered UVM Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate everything
  python generate_uvm.py --block block.yaml --vplan vplan.yaml --output ./generated

  # Generate only infrastructure (Phase A)
  python generate_uvm.py --block block.yaml --vplan vplan.yaml --output ./generated --phase-a-only

  # Generate only specific test cases
  python generate_uvm.py --block block.yaml --vplan vplan.yaml --output ./generated --test-ids TC_001 TC_002
        """
    )
    
    # Required arguments
    parser.add_argument('--block', required=True, help='Path to Block YAML file')
    parser.add_argument('--vplan', required=True, help='Path to Vplan YAML file')
    parser.add_argument('--output', required=True, help='Output directory')
    
    # Optional arguments
    parser.add_argument('--examples', default='../OTHER REQUIRED FILES',
                        help='Path to example files directory')
    parser.add_argument('--uvc-lib', default='../uvc',
                        help='Path to UVC library directory')
    parser.add_argument('--api-key', help='LLM API key (or set ANTHROPIC_API_KEY env var)')
    parser.add_argument('--provider', default='anthropic', choices=['anthropic', 'openai'],
                        help='LLM provider')
    parser.add_argument('--model', help='LLM model name')
    
    # Phase control
    parser.add_argument('--phase-a-only', action='store_true',
                        help='Only run Phase A (infrastructure generation)')
    parser.add_argument('--phase-b-only', action='store_true',
                        help='Only run Phase B (test case generation)')
    parser.add_argument('--test-ids', nargs='+',
                        help='Specific test case IDs to generate')
    
    args = parser.parse_args()
    
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
    print("UVM Generator - LLM-Powered Code Generation")
    print("=" * 60)
    print(f"Block YAML: {args.block}")
    print(f"Vplan YAML: {args.vplan}")
    print(f"Output Dir: {args.output}")
    print(f"Provider:   {args.provider}")
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
            model=args.model
        )
        
        env_content = ""
        vseqr_content = ""
        
        # Run Phase A
        if not args.phase_b_only:
            env_content, vseqr_content = generator.run_phase_a()
        
        # Run Phase B
        if not args.phase_a_only:
            generator.run_phase_b(
                env_content=env_content,
                vseqr_content=vseqr_content,
                test_ids=args.test_ids
            )
            
            # Generate package
            generator.generate_package()
        
        # Print summary
        generator.print_summary()
        
        print("\n✅ Generation complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
