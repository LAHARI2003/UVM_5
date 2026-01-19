#!/usr/bin/env python3
"""
Run UVM Generator with OpenAI GPT model
Uses the example.yaml (single test case) for testing

SETUP:
1. Edit env_config.txt and add your OpenAI API key
2. Run: python run_with_openai.py
"""

import os
import sys
from pathlib import Path

# Load API key from env_config.txt
def load_env_config():
    env_file = Path(__file__).parent / "env_config.txt"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value and value != 'your-openai-api-key-here':
                        os.environ[key] = value
                        print(f"  Loaded: {key}={value[:10]}...")

print("=" * 60)
print("UVM Generator - OpenAI GPT Run")
print("=" * 60)

# Load environment
print("\nLoading API key from env_config.txt...")
load_env_config()

# Check API key
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key or api_key == 'your-openai-api-key-here':
    print("\n[ERROR] OpenAI API key not set!")
    print("   Please edit env_config.txt and add your API key")
    print("   Then run this script again")
    sys.exit(1)

print(f"  API Key loaded: {api_key[:15]}...")

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after setting up environment
from utils.parser import BlockYAMLParser, VplanYAMLParser, load_uvc_mapping, load_settings
from utils.llm_client import LLMClient
from utils.file_utils import FileManager, collect_example_files
from prompts.ip_infra_prompts import (
    get_env_prompt, 
    get_virtual_sequencer_prompt,
    get_interface_prompt,
    get_package_prompt
)
from prompts.test_case_prompts import get_test_prompt, get_vseq_prompt

def main():
    # Paths
    base_dir = Path(__file__).parent.parent
    block_yaml_path = base_dir / "model_files" / "Block_YAML_file.txt"
    vplan_yaml_path = base_dir / "Test_case_File" / "example.yaml"  # Using example.yaml (1 test case)
    example_dir = base_dir / "OTHER REQUIRED FILES"
    output_dir = Path(__file__).parent / "output"
    config_dir = Path(__file__).parent / "config"
    
    print(f"\nConfiguration:")
    print(f"  Block YAML:  {block_yaml_path}")
    print(f"  Vplan YAML:  {vplan_yaml_path}")
    print(f"  Examples:    {example_dir}")
    print(f"  Output:      {output_dir}")
    
    # ═══════════════════════════════════════════════════════════════
    # Initialize
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("Initializing...")
    print("=" * 60)
    
    # Parse input files
    print("\n  Parsing Block YAML...")
    block_parser = BlockYAMLParser(str(block_yaml_path))
    block_yaml_content = block_yaml_path.read_text()
    print(f"    Block: {block_parser.get_block_name()}")
    
    print("\n  Parsing Vplan YAML...")
    vplan_parser = VplanYAMLParser(str(vplan_yaml_path))
    test_cases = vplan_parser.get_test_cases()
    print(f"    Test Cases: {len(test_cases)}")
    for tc in test_cases:
        print(f"      - {tc.get('TC_ID', 'Unknown')}")
    
    # Load examples
    print("\n  Loading example files...")
    examples = collect_example_files(str(example_dir))
    for key in examples:
        print(f"    Found: {key}")
    
    # Initialize LLM client (OpenAI with GPT-4.1)
    print("\n  Initializing OpenAI client...")
    model = "gpt-5.2-2025-12-11"  # Using GPT-4.1
    print(f"    Model: {model}")
    
    try:
        llm = LLMClient(provider="openai", api_key=api_key, model=model)
        print("    [OK] OpenAI client initialized")
    except Exception as e:
        print(f"    [FAIL] Failed to initialize OpenAI client: {e}")
        return 1
    
    # Setup output directories
    file_manager = FileManager(str(output_dir))
    file_manager.setup_directories()
    print(f"\n  Output directory ready: {output_dir}")
    
    # Naming
    env_class_name = "p18_dimc_tile_wrap_env"
    vseqr_class_name = "p18_dimc_tile_wrap_virtual_sequencer"
    interface_name = "dimc_tilewrap_if"
    package_name = "dimc_tile_wrap_pkg"
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE A: Generate IP Infrastructure
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("PHASE A: Generating IP Infrastructure")
    print("=" * 60)
    
    # Generate Environment
    print("\n[1/3] Generating Environment...")
    env_prompt = get_env_prompt(
        block_yaml=block_yaml_content,
        uvc_info="",  # Simplified for this run
        example_env=examples.get('env', ''),
        env_class_name=env_class_name,
        vseqr_class_name=vseqr_class_name
    )
    
    try:
        env_content = llm.generate(env_prompt)
        env_path = file_manager.write_file(
            f"ip_infra/env/{env_class_name}.sv",
            env_content
        )
        print(f"  [OK] Created: {env_path}")
    except Exception as e:
        print(f"  [FAIL] Error generating env: {e}")
        env_content = ""
    
    # Generate Virtual Sequencer
    print("\n[2/3] Generating Virtual Sequencer...")
    vseqr_prompt = get_virtual_sequencer_prompt(
        block_yaml=block_yaml_content,
        example_vseqr=examples.get('vseqr', ''),
        vseqr_class_name=vseqr_class_name,
        dut_if_name=interface_name
    )
    
    try:
        vseqr_content = llm.generate(vseqr_prompt)
        vseqr_path = file_manager.write_file(
            f"ip_infra/virtual_sequencer/{vseqr_class_name}.sv",
            vseqr_content
        )
        print(f"  [OK] Created: {vseqr_path}")
    except Exception as e:
        print(f"  [FAIL] Error generating vseqr: {e}")
        vseqr_content = ""
    
    # Generate Interface
    print("\n[3/3] Generating Interface...")
    interface_prompt = get_interface_prompt(
        block_yaml=block_yaml_content,
        example_interface=examples.get('interface', ''),
        interface_name=interface_name,
        clock_name="dimc_tilewrap_clk",
        reset_name="resetn"
    )
    
    try:
        interface_content = llm.generate(interface_prompt)
        interface_path = file_manager.write_file(
            f"ip_infra/interface/{interface_name}.sv",
            interface_content
        )
        print(f"  [OK] Created: {interface_path}")
    except Exception as e:
        print(f"  [FAIL] Error generating interface: {e}")
    
    print("\n[OK] Phase A complete!")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE B: Generate Test Cases
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("PHASE B: Generating Test Cases")
    print("=" * 60)
    
    vseq_files = []
    test_files = []
    
    for i, tc in enumerate(test_cases, 1):
        tc_id = tc.get('TC_ID', f'unknown_{i}')
        print(f"\n[{i}/{len(test_cases)}] Generating: {tc_id}")
        
        # Extract configuration
        tc_config = vplan_parser.extract_config(tc)
        tc_config['mode_int'] = vplan_parser.get_mode_int(tc_config['mode'])
        tc_config['sign_int'] = vplan_parser.get_sign_int(tc_config['sign_8b'])
        
        print(f"  Config: mode={tc_config['mode']}, sign={tc_config['sign_8b']}, ps={tc_config['ps_phase']}")
        
        # Generate test file
        print("  Generating _test.sv...")
        test_prompt = get_test_prompt(
            tc_config=tc_config,
            example_test=examples.get('test', ''),
            env_class=env_class_name,
            vseqr_class=vseqr_class_name,
            dut_if_name=interface_name
        )
        
        try:
            test_content = llm.generate(test_prompt)
            test_path = file_manager.write_file(
                f"tests/tests/{tc_id}_test.sv",
                test_content
            )
            test_files.append(f"{tc_id}_test.sv")
            print(f"    [OK] {tc_id}_test.sv")
        except Exception as e:
            print(f"    [FAIL] Error: {e}")
        
        # Generate vseq file
        print("  Generating _vseq.sv...")
        vseq_prompt = get_vseq_prompt(
            tc_config=tc_config,
            example_vseq=examples.get('vseq', ''),
            vseqr_class=vseqr_class_name,
            active_uvcs=tc.get('Active_UVCs', []),
            uvc_mapping={},
            generated_vseqr=vseqr_content,  # Pass generated virtual sequencer for context
            c_model_usage=""  # Will use default from prompt
        )
        
        try:
            vseq_content = llm.generate(vseq_prompt)
            vseq_path = file_manager.write_file(
                f"tests/virtual_sequences/{tc_id}_vseq.sv",
                vseq_content
            )
            vseq_files.append(f"{tc_id}_vseq.sv")
            print(f"    [OK] {tc_id}_vseq.sv")
        except Exception as e:
            print(f"    [FAIL] Error: {e}")
    
    print(f"\n[OK] Phase B complete! Generated {len(test_files)} test cases")
    
    # ═══════════════════════════════════════════════════════════════
    # Generate Package
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("Generating Package File")
    print("=" * 60)
    
    package_prompt = get_package_prompt(
        block_yaml=block_yaml_content,
        example_package=examples.get('package', ''),
        package_name=package_name,
        vseq_includes=vseq_files,
        test_includes=test_files,
        env_file=f"{env_class_name}.sv",
        vseqr_file=f"{vseqr_class_name}.sv",
        scoreboard_file="p18_dimc_tile_wrap_scoreboard.sv"
    )
    
    try:
        package_content = llm.generate(package_prompt)
        package_path = file_manager.write_file(
            f"ip_infra/pkg/{package_name}.sv",
            package_content
        )
        print(f"  [OK] Created: {package_path}")
    except Exception as e:
        print(f"  [FAIL] Error generating package: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(file_manager.generate_summary())
    
    print("\n[SUCCESS] All files generated successfully!")
    print(f"\nOutput location: {output_dir}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
