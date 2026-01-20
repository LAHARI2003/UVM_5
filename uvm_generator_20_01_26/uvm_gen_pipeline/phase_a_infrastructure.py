"""
Phase A: IP Infrastructure Generation
Generates one-time IP-level UVM components: interface, virtual sequencer, environment, scoreboard.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel

from config import Config
from llm_client import UVMGeneratorLLM, extract_code_from_response
from prompts import (
    INTERFACE_GENERATION_PROMPT,
    VIRTUAL_SEQUENCER_PROMPT,
    ENVIRONMENT_PROMPT,
    SCOREBOARD_PROMPT,
    build_context,
    format_prompt
)

console = Console()


class PhaseAInfrastructure:
    """Generates IP-level infrastructure components."""
    
    def __init__(
        self,
        config: Config,
        llm: UVMGeneratorLLM,
        block_config: Dict,
        uvc_mapping: Dict,
        model_info: Dict
    ):
        self.config = config
        self.llm = llm
        self.block_config = block_config
        self.uvc_mapping = uvc_mapping
        self.model_info = model_info
        self.generated_files: List[Path] = []
        
        # Derive names from block config
        self.block_name = block_config.get('name', 'dut')
        self.short_name = self._get_short_name()
        
    def _get_short_name(self) -> str:
        """Get a short name for the block (for file naming)."""
        name = self.block_name.lower()
        # Remove common suffixes
        for suffix in ['_wrapper', '_wrap', '_m', '_top']:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        return name
    
    def run(self) -> List[Path]:
        """
        Execute Phase A: Generate IP infrastructure.
        
        Returns:
            List of generated file paths
        """
        console.print(Panel("[bold cyan]Phase A: IP Infrastructure Generation[/bold cyan]"))
        
        output_dir = self.config.pipeline.output_dir / "ip"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load example files for few-shot learning
        examples = self._load_example_files()
        context = build_context(self.block_config, self.uvc_mapping, self.model_info)
        
        # A.1 Generate Interface
        self._generate_interface(output_dir, context, examples.get('interface'))
        
        # A.2 Generate Virtual Sequencer
        self._generate_virtual_sequencer(output_dir, context, examples.get('virtual_sequencer'))
        
        # A.3 Generate Environment
        self._generate_environment(output_dir, context, examples.get('environment'))
        
        # A.4 Generate Scoreboard (optional)
        if self.config.pipeline.generate_scoreboard:
            self._generate_scoreboard(output_dir, context, examples.get('scoreboard'))
        
        console.print(f"[green]Phase A complete - Generated {len(self.generated_files)} files[/green]\n")
        
        return self.generated_files
    
    def _load_example_files(self) -> Dict[str, str]:
        """Load example files from golden reference for few-shot learning."""
        examples = {}
        golden_path = self.config.pipeline.golden_ref_path
        
        # Interface example
        interface_file = golden_path / "dimc_tile_DUT_files" / "interface" / "dimc_tile_wrap_if_interface.sv"
        if interface_file.exists():
            examples['interface'] = interface_file.read_text()
        
        # Virtual sequencer example
        vseqr_file = golden_path / "dimc_tile_DUT_files" / "virtual_sequencer" / "p18_dimc_tile_wrap_virtual_sequencer.sv"
        if vseqr_file.exists():
            examples['virtual_sequencer'] = vseqr_file.read_text()
        
        # Environment example
        env_file = golden_path / "dimc_tile_DUT_files" / "env" / "p18_dimc_tile_wrap_env.sv"
        if env_file.exists():
            examples['environment'] = env_file.read_text()
        
        return examples
    
    def _generate_interface(self, output_dir: Path, context: str, example: Optional[str]):
        """Generate the main DUT interface file."""
        console.print("  [A.1] Generating Interface...", end=" ")
        
        output_filename = f"{self.short_name}_if.sv"
        
        # Build interface list from UVC mapping
        interface_list = []
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            interface_list.append(f"- {name}: {info.get('kind', 'unknown')}")
        
        # Compute reset polarity text
        reset_polarity = 'Low' if self.block_config.get('reset_active_low', True) else 'High'
        
        prompt = format_prompt(
            INTERFACE_GENERATION_PROMPT,
            block_name=self.block_name,
            clock_name=self.block_config.get('clock_name', 'clk'),
            clock_freq=self.block_config.get('clock_freq', '100MHz'),
            reset_name=self.block_config.get('reset_name', 'resetn'),
            reset_polarity=reset_polarity,
            interface_list='\n'.join(interface_list),
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.generated_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")
    
    def _generate_virtual_sequencer(self, output_dir: Path, context: str, example: Optional[str]):
        """Generate the virtual sequencer file."""
        console.print("  [A.2] Generating Virtual Sequencer...", end=" ")
        
        output_filename = f"{self.short_name}_virtual_sequencer.sv"
        
        # Build sequencer list from UVC mapping
        sequencer_list = []
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            seqr_type = info.get('sequencer_type', 'uvm_sequencer')
            kind = info.get('kind', '')
            
            # Extract parameters from kind (e.g., "istream_env#(64)" -> "#(64)")
            params = ""
            if '#(' in kind:
                params = kind[kind.index('#'):]
                params = params.replace('_env', '_sequencer')
            
            sequencer_list.append(f"- {seqr_type}{params} seqr_{name.replace('m_', '').replace('_env', '')}")
        
        prompt = format_prompt(
            VIRTUAL_SEQUENCER_PROMPT,
            block_name=self.block_name,
            sequencer_list='\n'.join(sequencer_list),
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.generated_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")
    
    def _generate_environment(self, output_dir: Path, context: str, example: Optional[str]):
        """Generate the top-level environment file."""
        console.print("  [A.3] Generating Environment...", end=" ")
        
        output_filename = f"{self.short_name}_env.sv"
        
        # Build environment list
        env_list = []
        params_config = []
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            kind = info.get('kind', '')
            params = info.get('params', {})
            env_list.append(f"- {kind} {name}")
            if params:
                params_config.append(f"{name}: {params}")
        
        prompt = format_prompt(
            ENVIRONMENT_PROMPT,
            block_name=self.block_name,
            env_list='\n'.join(env_list),
            params_config='\n'.join(params_config) if params_config else "No special parameters",
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.generated_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")
    
    def _generate_scoreboard(self, output_dir: Path, context: str, example: Optional[str]):
        """Generate the scoreboard file."""
        console.print("  [A.4] Generating Scoreboard...", end=" ")
        
        output_filename = f"{self.short_name}_scoreboard.sv"
        
        # Get output data width from UVC mapping
        data_width = 64  # Default
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            if 'output' in name.lower() or 'ostream' in info.get('kind', '').lower():
                params = info.get('params', {})
                data_width = params.get('DATA_WIDTH', 64)
                break
        
        prompt = format_prompt(
            SCOREBOARD_PROMPT,
            block_name=self.block_name,
            expected_output_file="output_buffer_expected_out_psout_hex.txt",
            data_width=data_width,
            num_entries=32,
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.generated_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")


def run_phase_a(
    config: Config,
    llm: UVMGeneratorLLM,
    block_config: Dict,
    uvc_mapping: Dict,
    model_info: Dict
) -> List[Path]:
    """Convenience function to run Phase A."""
    phase = PhaseAInfrastructure(config, llm, block_config, uvc_mapping, model_info)
    return phase.run()
