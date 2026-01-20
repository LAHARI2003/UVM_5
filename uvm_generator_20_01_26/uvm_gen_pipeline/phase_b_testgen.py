"""
Phase B: Test Case Generation
Generates test files and virtual sequences for each test case in the Vplan.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import Config
from llm_client import UVMGeneratorLLM, extract_code_from_response
from parsers import TestCase
from prompts import (
    TEST_FILE_PROMPT,
    VIRTUAL_SEQUENCE_PROMPT,
    build_context,
    format_prompt
)

console = Console()


class PhaseBTestGeneration:
    """Generates test files and virtual sequences for each test case."""
    
    def __init__(
        self,
        config: Config,
        llm: UVMGeneratorLLM,
        block_config: Dict,
        test_cases: List[TestCase],
        uvc_mapping: Dict,
        model_info: Dict
    ):
        self.config = config
        self.llm = llm
        self.block_config = block_config
        self.test_cases = test_cases
        self.uvc_mapping = uvc_mapping
        self.model_info = model_info
        self.generated_files: List[Path] = []
        
        # Derive names
        self.block_name = block_config.get('name', 'dut')
        self.short_name = self._get_short_name()
        
    def _get_short_name(self) -> str:
        """Get a short name for the block."""
        name = self.block_name.lower()
        for suffix in ['_wrapper', '_wrap', '_m', '_top']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name
    
    def run(self) -> List[Path]:
        """
        Execute Phase B: Generate test cases.
        
        Returns:
            List of generated file paths
        """
        console.print(Panel("[bold cyan]Phase B: Test Case Generation[/bold cyan]"))
        
        output_dir = self.config.pipeline.output_dir / "tests"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load example files
        examples = self._load_example_files()
        context = build_context(self.block_config, self.uvc_mapping, self.model_info)
        
        # Generate for each test case
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Generating {len(self.test_cases)} test cases...",
                total=len(self.test_cases)
            )
            
            for i, test_case in enumerate(self.test_cases, 1):
                progress.update(task, description=f"[{i}/{len(self.test_cases)}] {test_case.tc_id}")
                
                # B.1 Generate test file
                self._generate_test_file(output_dir, test_case, context, examples.get('test'))
                
                # B.2 Generate virtual sequence
                self._generate_virtual_sequence(output_dir, test_case, context, examples.get('vseq'))
                
                progress.advance(task)
        
        console.print(f"[green]Phase B complete - Generated {len(self.generated_files)} files[/green]\n")
        
        return self.generated_files
    
    def _load_example_files(self) -> Dict[str, str]:
        """Load example test files for few-shot learning."""
        examples = {}
        golden_path = self.config.pipeline.golden_ref_path
        example_dir = golden_path / "Example_test_case_files"
        
        # Test file example
        test_file = example_dir / "CI_TC_005_mode0_sign0_PS_FIRST_test.sv"
        if test_file.exists():
            examples['test'] = test_file.read_text()
        
        # Virtual sequence example
        vseq_file = example_dir / "CI_TC_005_mode0_sign0_PS_FIRST_vseq.sv"
        if vseq_file.exists():
            examples['vseq'] = vseq_file.read_text()
        
        return examples
    
    def _generate_test_file(
        self,
        output_dir: Path,
        test_case: TestCase,
        context: str,
        example: Optional[str]
    ):
        """Generate the test file for a test case."""
        tc_id = test_case.tc_id
        output_filename = f"{tc_id}_test.sv"
        
        # Build active UVCs list
        active_uvcs = '\n'.join([f"- {uvc}" for uvc in test_case.active_uvcs])
        
        prompt = format_prompt(
            TEST_FILE_PROMPT,
            tc_id=tc_id,
            env_class=f"{self.short_name}_env",
            vseq_class=f"{tc_id}_vseq",
            active_uvcs=active_uvcs,
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.generated_files.append(output_path)
    
    def _generate_virtual_sequence(
        self,
        output_dir: Path,
        test_case: TestCase,
        context: str,
        example: Optional[str]
    ):
        """Generate the virtual sequence for a test case."""
        tc_id = test_case.tc_id
        output_filename = f"{tc_id}_vseq.sv"
        
        # Build test configuration
        test_config = self._build_test_config(test_case)
        
        # Build register configuration
        register_config = self._build_register_config(test_case)
        
        # Build stimulus configuration
        stimulus_config = self._build_stimulus_config(test_case)
        
        # Build sequence list
        sequence_list = self._build_sequence_list(test_case)
        
        prompt = format_prompt(
            VIRTUAL_SEQUENCE_PROMPT,
            tc_id=tc_id,
            test_config=test_config,
            register_config=register_config,
            stimulus_config=stimulus_config,
            sequence_list=sequence_list,
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.generated_files.append(output_path)
    
    def _build_test_config(self, test_case: TestCase) -> str:
        """Build test configuration string from test case."""
        config_lines = [
            f"Test ID: {test_case.tc_id}",
            f"Active UVCs: {', '.join(test_case.active_uvcs)}",
        ]
        
        # Extract mode, sign, PS flags from stimulus
        regbank = test_case.stimulus.regbank_program
        if regbank:
            config_lines.append(f"Mode: {regbank.get('mode', '00')}")
            config_lines.append(f"Sign_8b: {regbank.get('sign_8b', 'dont_care')}")
            config_lines.append(f"PS Phase: {regbank.get('ps_phase', 'PS_FIRST')}")
        
        return '\n'.join(config_lines)
    
    def _build_register_config(self, test_case: TestCase) -> str:
        """Build register configuration string."""
        regbank = test_case.stimulus.regbank_program
        
        if not regbank:
            return "No register configuration specified"
        
        # Standard register mapping
        mapping = """Register bit mapping:
- register[5:0]   = K_DIM
- register[6]     = START_COMPUTE
- register[7]     = COMPE
- register[8]     = PS_FIRST
- register[9]     = PS_MODE
- register[10]    = PS_LAST
- register[12:11] = MODE
- register[14:13] = sign_8b
- register[15]    = CONT_COMP
- register[23:16] = iteration"""
        
        config_lines = [mapping]
        config_lines.append(f"\nValues for this test:")
        config_lines.append(f"- MODE = {regbank.get('mode', '00')}")
        config_lines.append(f"- sign_8b = {regbank.get('sign_8b', '00')}")
        
        ps_phase = regbank.get('ps_phase', 'PS_FIRST')
        if ps_phase == 'PS_FIRST':
            config_lines.append("- PS_FIRST=1, PS_MODE=0, PS_LAST=0")
        elif ps_phase == 'PS_MODE':
            config_lines.append("- PS_FIRST=0, PS_MODE=1, PS_LAST=0")
        elif ps_phase == 'PS_LAST':
            config_lines.append("- PS_FIRST=0, PS_MODE=0, PS_LAST=1")
        
        return '\n'.join(config_lines)
    
    def _build_stimulus_config(self, test_case: TestCase) -> str:
        """Build stimulus configuration string."""
        stimulus = test_case.stimulus
        config_lines = []
        
        # Input provisioning
        if stimulus.input_provisioning:
            config_lines.append("Input Provisioning:")
            for target, info in stimulus.input_provisioning.items():
                if isinstance(info, dict):
                    pattern = info.get('pattern_bin', 'RANDOM')
                    notes = info.get('notes', '')
                    config_lines.append(f"  - {target}: pattern={pattern}")
                    if notes:
                        config_lines.append(f"    Notes: {notes}")
        
        # Trigger compute
        if stimulus.trigger_compute:
            config_lines.append(f"\nTrigger Compute:")
            config_lines.append(f"  {stimulus.trigger_compute.get('notes', '')}")
        
        # Output read
        if stimulus.output_read:
            config_lines.append(f"\nOutput Read:")
            for target, info in stimulus.output_read.items():
                if isinstance(info, dict):
                    config_lines.append(f"  - {target}: {info.get('notes', '')}")
        
        return '\n'.join(config_lines) if config_lines else "Default stimulus configuration"
    
    def _build_sequence_list(self, test_case: TestCase) -> str:
        """Build list of sequences to use based on active UVCs."""
        sequences = []
        
        for uvc in test_case.active_uvcs:
            # Map UVC to appropriate sequences
            if 'register' in uvc.lower() or 'computation' in uvc.lower():
                sequences.append("- register_configure_write_seq for register programming")
            elif 'kernel' in uvc.lower():
                sequences.append("- dpmem_directed_write_sequence#(64,9) for kernel memory")
            elif 'feature' in uvc.lower():
                sequences.append("- istream_directed_write_sequence#(64) for feature buffer")
            elif 'psin' in uvc.lower():
                sequences.append("- istream_directed_write_sequence#(32) for psin")
            elif 'addin' in uvc.lower():
                sequences.append("- spmem_directed_write_sequence#(64,4) for addin memory")
            elif 'output' in uvc.lower():
                sequences.append("- ostream_random_burst_read_sequence#(64) for output buffer")
        
        return '\n'.join(sequences) if sequences else "Standard sequences based on active UVCs"


def run_phase_b(
    config: Config,
    llm: UVMGeneratorLLM,
    block_config: Dict,
    test_cases: List[TestCase],
    uvc_mapping: Dict,
    model_info: Dict
) -> List[Path]:
    """Convenience function to run Phase B."""
    phase = PhaseBTestGeneration(config, llm, block_config, test_cases, uvc_mapping, model_info)
    return phase.run()
