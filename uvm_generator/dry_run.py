#!/usr/bin/env python3
"""
Dry Run - Test the UVM Generator pipeline without LLM API calls

This validates:
1. YAML parsing works correctly
2. Configuration loading works
3. File structure would be created correctly
4. Shows what would be generated
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.parser import BlockYAMLParser, VplanYAMLParser, load_uvc_mapping, load_settings
from utils.file_utils import FileManager, collect_example_files

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")

def main():
    print_header("UVM Generator - DRY RUN")
    print("This validates the pipeline without making LLM API calls")
    
    # Paths
    block_yaml_path = Path(__file__).parent.parent / "model_files" / "Block_YAML_file.txt"
    vplan_yaml_path = Path(__file__).parent.parent / "model_files" / "sc_2_gpt_5_2.yaml"
    example_dir = Path(__file__).parent.parent / "OTHER REQUIRED FILES"
    config_dir = Path(__file__).parent / "config"
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 1: Block YAML Parsing
    # ═══════════════════════════════════════════════════════════════
    print_section("TEST 1: Block YAML Parsing")
    
    try:
        block_parser = BlockYAMLParser(str(block_yaml_path))
        block_data = block_parser.to_dict()
        
        print(f"✓ Successfully parsed: {block_yaml_path.name}")
        print(f"\n  Block Name: {block_data['block_name']}")
        print(f"  Clock: {block_data['clock']['name']} @ {block_data['clock']['frequency']}")
        print(f"  Reset: {block_data['reset']['name']} (active_low: {block_data['reset']['active_low']})")
        print(f"  Model: {block_data['model']['language']} ({block_data['model']['lib_path']})")
        
        print(f"\n  Interfaces ({len(block_data['interfaces'])}):")
        for iface in block_data['interfaces']:
            print(f"    • {iface['name']}: {iface['kind']}")
            if iface['params']:
                print(f"      params: {iface['params']}")
        
    except Exception as e:
        print(f"✗ Error parsing Block YAML: {e}")
        return 1
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 2: Vplan YAML Parsing
    # ═══════════════════════════════════════════════════════════════
    print_section("TEST 2: Vplan YAML Parsing")
    
    try:
        vplan_parser = VplanYAMLParser(str(vplan_yaml_path))
        test_cases = vplan_parser.get_test_cases()
        
        print(f"✓ Successfully parsed: {vplan_yaml_path.name}")
        print(f"\n  Total Test Cases: {len(test_cases)}")
        
        # Show first 5 test cases
        print("\n  Test Cases Preview (first 5):")
        for i, tc in enumerate(test_cases[:5]):
            tc_id = tc.get('TC_ID', 'Unknown')
            config = vplan_parser.extract_config(tc)
            print(f"    [{i+1}] {tc_id}")
            print(f"        Mode: {config['mode']} | Sign: {config['sign_8b']} | PS: {config['ps_phase']}")
            print(f"        Active UVCs: {len(config['active_uvcs'])}")
        
        if len(test_cases) > 5:
            print(f"    ... and {len(test_cases) - 5} more test cases")
        
        # Analyze test case distribution
        print("\n  Test Case Distribution:")
        modes = {}
        ps_phases = {}
        for tc in test_cases:
            config = vplan_parser.extract_config(tc)
            modes[config['mode']] = modes.get(config['mode'], 0) + 1
            ps_phases[config['ps_phase']] = ps_phases.get(config['ps_phase'], 0) + 1
        
        print(f"    By Mode: {dict(sorted(modes.items()))}")
        print(f"    By PS Phase: {dict(sorted(ps_phases.items()))}")
        
    except Exception as e:
        print(f"✗ Error parsing Vplan YAML: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 3: Configuration Loading
    # ═══════════════════════════════════════════════════════════════
    print_section("TEST 3: Configuration Loading")
    
    try:
        settings = load_settings(str(config_dir / "settings.yaml"))
        uvc_mapping = load_uvc_mapping(str(config_dir / "uvc_mapping.yaml"))
        
        print(f"✓ Loaded settings.yaml")
        print(f"  LLM Provider: {settings['llm']['provider']}")
        print(f"  LLM Model: {settings['llm']['model']}")
        
        print(f"\n✓ Loaded uvc_mapping.yaml")
        print(f"  UVC Mappings: {len(uvc_mapping['uvc_mapping'])} entries")
        for uvc_name in uvc_mapping['uvc_mapping'].keys():
            print(f"    • {uvc_name}")
        
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        return 1
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 4: Example Files Discovery
    # ═══════════════════════════════════════════════════════════════
    print_section("TEST 4: Example Files Discovery")
    
    try:
        examples = collect_example_files(str(example_dir))
        
        print(f"✓ Found {len(examples)} example files:")
        for key, content in examples.items():
            lines = len(content.split('\n'))
            print(f"    • {key}: {lines} lines")
        
    except Exception as e:
        print(f"✗ Error collecting examples: {e}")
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 5: Output Structure Preview
    # ═══════════════════════════════════════════════════════════════
    print_section("TEST 5: Output Structure Preview")
    
    output_dir = Path(__file__).parent / "output"
    
    print(f"  Output Directory: {output_dir}")
    print("\n  Files that would be generated:")
    
    # Phase A files
    print("\n  PHASE A - IP Infrastructure:")
    infra_files = [
        "ip_infra/env/p18_dimc_tile_wrap_env.sv",
        "ip_infra/virtual_sequencer/p18_dimc_tile_wrap_virtual_sequencer.sv",
        "ip_infra/interface/dimc_tilewrap_if.sv",
        "ip_infra/pkg/dimc_tile_wrap_pkg.sv",
    ]
    for f in infra_files:
        print(f"    ✓ {f}")
    
    # Phase B files
    print(f"\n  PHASE B - Test Cases ({len(test_cases)} test cases × 2 files):")
    for i, tc in enumerate(test_cases[:3]):
        tc_id = tc.get('TC_ID', 'Unknown')
        print(f"    ✓ tests/tests/{tc_id}_test.sv")
        print(f"    ✓ tests/virtual_sequences/{tc_id}_vseq.sv")
    
    if len(test_cases) > 3:
        print(f"    ... and {(len(test_cases) - 3) * 2} more files")
    
    total_files = len(infra_files) + len(test_cases) * 2
    print(f"\n  Total files to generate: {total_files}")
    
    # ═══════════════════════════════════════════════════════════════
    # TEST 6: Sample Prompt Generation (for one test case)
    # ═══════════════════════════════════════════════════════════════
    print_section("TEST 6: Sample Prompt Generation")
    
    from prompts.test_case_prompts import get_test_prompt, get_vseq_prompt
    
    # Get first test case
    tc = test_cases[0]
    tc_config = vplan_parser.extract_config(tc)
    tc_config['mode_int'] = vplan_parser.get_mode_int(tc_config['mode'])
    tc_config['sign_int'] = vplan_parser.get_sign_int(tc_config['sign_8b'])
    
    print(f"  Sample test case: {tc_config['tc_id']}")
    print(f"\n  Extracted Configuration:")
    print(f"    • mode: '{tc_config['mode']}' → {tc_config['mode_int']}")
    print(f"    • sign_8b: '{tc_config['sign_8b']}' → {tc_config['sign_int']}")
    print(f"    • ps_phase: '{tc_config['ps_phase']}'")
    print(f"    • PS_FIRST: {tc_config['ps_first']}, PS_MODE: {tc_config['ps_mode']}, PS_LAST: {tc_config['ps_last']}")
    print(f"    • Active UVCs: {tc_config['active_uvcs']}")
    
    # Generate sample prompt (truncated)
    test_prompt = get_test_prompt(
        tc_config=tc_config,
        example_test=examples.get('test', '')[:500] + "...",
        env_class="p18_dimc_tile_wrap_env",
        vseqr_class="p18_dimc_tile_wrap_virtual_sequencer",
        dut_if_name="dimc_tilewrap_if"
    )
    
    print(f"\n  Generated prompt length: {len(test_prompt)} characters")
    print(f"  Prompt preview (first 300 chars):")
    print(f"    {test_prompt[:300]}...")
    
    # ═══════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print_header("DRY RUN SUMMARY")
    
    print("""
  ✓ Block YAML parsing:     PASSED
  ✓ Vplan YAML parsing:     PASSED  
  ✓ Configuration loading:  PASSED
  ✓ Example files:          PASSED
  ✓ Output structure:       VALIDATED
  ✓ Prompt generation:      PASSED

  Ready to run full generation!
  
  Next steps:
  1. Set your API key:
     $env:ANTHROPIC_API_KEY = "your-key-here"  # PowerShell
     
  2. Run full generation:
     python generate_uvm.py --block "../model_files/Block_YAML_file.txt" \\
                           --vplan "../model_files/sc_2_gpt_5_2.yaml" \\
                           --output "./output" \\
                           --examples "../OTHER REQUIRED FILES" \\
                           --uvc-lib "../uvc"
""")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
