#!/usr/bin/env python3
"""
Example script showing programmatic usage of the UVM Generator Pipeline.

This demonstrates how to use the pipeline as a library rather than CLI.
"""

import os
from pathlib import Path

# Ensure we have the API key
# os.environ['OPENAI_API_KEY'] = 'your-api-key-here'  # Uncomment and set if needed

from config import load_config
from llm_client import UVMGeneratorLLM
from phase0_preprocess import run_phase0
from phase_a_infrastructure import run_phase_a
from phase_b_testgen import run_phase_b
from phase_c_package import run_phase_c


def run_pipeline():
    """Run the complete UVM generation pipeline."""
    
    # Define paths relative to this script
    base_path = Path(__file__).parent.parent
    
    # Load configuration
    config = load_config(
        vplan_file=str(base_path / "Golden_reference_files" / "model_files" / "Vplan.yaml"),
        block_yaml_file=str(base_path / "Golden_reference_files" / "model_files" / "Block_YAML_file.txt"),
        model_cpp_file=str(base_path / "Golden_reference_files" / "model_files" / "psout_ac_fixed_14_11_25.cpp"),
        output_dir=str(base_path / "uvm_gen_pipeline" / "generated"),
        uvc_path=str(base_path / "uvc"),
        golden_ref_path=str(base_path / "Golden_reference_files")
    )
    
    # Validate configuration
    config.validate()
    
    # Initialize LLM client
    llm = UVMGeneratorLLM(config.openai)
    
    print("=" * 60)
    print("UVM Test Case Generator - Programmatic Example")
    print("=" * 60)
    
    # Phase 0: Preprocessing
    print("\n[Phase 0] Running preprocessing...")
    block_config, test_cases, model_info, uvc_mapping = run_phase0(config)
    
    print(f"  Block: {block_config.get('name', 'unknown')}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  UVCs: {len(uvc_mapping.get('uvcs', {}))}")
    
    # Phase A: IP Infrastructure
    print("\n[Phase A] Generating IP infrastructure...")
    ip_files = run_phase_a(config, llm, block_config, uvc_mapping, model_info)
    print(f"  Generated {len(ip_files)} files")
    
    # Phase B: Test Case Generation
    print("\n[Phase B] Generating test cases...")
    test_files = run_phase_b(config, llm, block_config, test_cases, uvc_mapping, model_info)
    print(f"  Generated {len(test_files)} files")
    
    # Phase C: Package & Integration
    print("\n[Phase C] Generating package and integration...")
    all_files = ip_files + test_files
    pkg_files = run_phase_c(config, llm, block_config, uvc_mapping, all_files)
    print(f"  Generated {len(pkg_files)} files")
    
    # Summary
    total_files = ip_files + test_files + pkg_files
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Total files generated: {len(total_files)}")
    print(f"Output directory: {config.pipeline.output_dir}")
    print("\nGenerated files:")
    for f in total_files:
        print(f"  - {f.name}")
    
    return total_files


def run_phase0_only():
    """Run only the preprocessing phase (useful for validation)."""
    
    base_path = Path(__file__).parent.parent
    
    config = load_config(
        vplan_file=str(base_path / "Golden_reference_files" / "model_files" / "Vplan.yaml"),
        block_yaml_file=str(base_path / "Golden_reference_files" / "model_files" / "Block_YAML_file.txt"),
        model_cpp_file=str(base_path / "Golden_reference_files" / "model_files" / "psout_ac_fixed_14_11_25.cpp"),
        output_dir=str(base_path / "uvm_gen_pipeline" / "generated"),
        uvc_path=str(base_path / "uvc"),
        golden_ref_path=str(base_path / "Golden_reference_files")
    )
    
    print("Running Phase 0 only (preprocessing)...")
    block_config, test_cases, model_info, uvc_mapping = run_phase0(config)
    
    print("\n--- Block Configuration ---")
    print(f"Name: {block_config.get('name')}")
    print(f"Clock: {block_config.get('clock_name')}")
    print(f"Reset: {block_config.get('reset_name')}")
    print(f"Interfaces: {len(block_config.get('interfaces', []))}")
    
    print("\n--- Test Cases ---")
    for tc in test_cases:
        print(f"  {tc.tc_id}")
        print(f"    Active UVCs: {tc.active_uvcs}")
    
    print("\n--- UVC Mapping ---")
    for name, info in uvc_mapping.get('uvcs', {}).items():
        print(f"  {name}: {info.get('kind')}")
    
    return block_config, test_cases, model_info, uvc_mapping


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--phase0':
        run_phase0_only()
    else:
        run_pipeline()
