"""
Phase C: Package & Integration
Generates the package file and file list for compilation.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel

from config import Config
from llm_client import UVMGeneratorLLM, extract_code_from_response
from prompts import PACKAGE_PROMPT, TESTBENCH_PROMPT, format_prompt, build_context

console = Console()


class PhaseCPackage:
    """Generates package file and integration artifacts."""
    
    def __init__(
        self,
        config: Config,
        llm: UVMGeneratorLLM,
        block_config: Dict,
        uvc_mapping: Dict,
        generated_files: List[Path]
    ):
        self.config = config
        self.llm = llm
        self.block_config = block_config
        self.uvc_mapping = uvc_mapping
        self.generated_files = generated_files
        self.output_files: List[Path] = []
        
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
        Execute Phase C: Generate package and integration files.
        
        Returns:
            List of generated file paths
        """
        console.print(Panel("[bold cyan]Phase C: Package & Integration[/bold cyan]"))
        
        output_dir = self.config.pipeline.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load example files
        examples = self._load_example_files()
        context = build_context(self.block_config, self.uvc_mapping)
        
        # C.1 Generate Package File
        if self.config.pipeline.generate_package:
            self._generate_package(output_dir, context, examples.get('package'))
        
        # C.2 Generate File List
        self._generate_filelist(output_dir)
        
        # C.3 Generate Testbench (optional - can use LLM or template)
        self._generate_testbench_template(output_dir, context, examples.get('testbench'))
        
        console.print(f"[green]Phase C complete - Generated {len(self.output_files)} files[/green]\n")
        
        return self.output_files
    
    def _load_example_files(self) -> Dict[str, str]:
        """Load example files for few-shot learning."""
        examples = {}
        golden_path = self.config.pipeline.golden_ref_path
        
        # Package example
        pkg_file = golden_path / "dimc_tile_DUT_files" / "pkg" / "dimc_tile_wrap_package.sv"
        if pkg_file.exists():
            examples['package'] = pkg_file.read_text()
        
        # Testbench example
        tb_file = golden_path / "dimc_tile_DUT_files" / "tb" / "P18_TILE_WRAPPER_tb.sv"
        if tb_file.exists():
            examples['testbench'] = tb_file.read_text()
        
        return examples
    
    def _generate_package(self, output_dir: Path, context: str, example: Optional[str]):
        """Generate the SystemVerilog package file."""
        console.print("  [C.1] Generating Package...", end=" ")
        
        output_filename = f"{self.short_name}_pkg.sv"
        
        # Build UVC package list
        uvc_packages = []
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            uvc_type = info.get('type', '')
            # Map UVC type to package name
            pkg_name = uvc_type.replace('_uvc', '_pkg')
            if pkg_name not in uvc_packages:
                uvc_packages.append(f"- {pkg_name}")
        
        # Build file list (order matters for dependencies)
        file_list = self._get_ordered_file_list()
        
        prompt = format_prompt(
            PACKAGE_PROMPT,
            block_name=self.block_name,
            uvc_packages='\n'.join(uvc_packages),
            file_list='\n'.join([f"- {f}" for f in file_list]),
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.output_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")
    
    def _generate_filelist(self, output_dir: Path):
        """Generate the compilation file list."""
        console.print("  [C.2] Generating File List...", end=" ")
        
        output_filename = "files.f"
        
        lines = [
            "# UVM Test Case Generator - File List",
            "# Auto-generated - Do not edit manually",
            "",
            "# UVM Package",
            "+incdir+$UVM_HOME/src",
            "$UVM_HOME/src/uvm_pkg.sv",
            "",
            "# UVC Libraries",
        ]
        
        # Add UVC paths
        uvc_path = self.config.pipeline.uvc_library_path
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            uvc_type = info.get('type', '')
            if uvc_type:
                lines.append(f"+incdir+{uvc_path}/{uvc_type}")
                lines.append(f"{uvc_path}/{uvc_type}/pkg/{uvc_type.replace('_uvc', '_pkg')}.sv")
        
        lines.append("")
        lines.append("# Generated IP Files")
        lines.append(f"+incdir+{output_dir}/ip")
        
        # Add generated IP files
        for f in self.generated_files:
            if '/ip/' in str(f) or '\\ip\\' in str(f):
                lines.append(str(f))
        
        lines.append("")
        lines.append("# Generated Virtual Sequences")
        lines.append(f"+incdir+{output_dir}/virtual_sequences")
        
        # Add generated virtual sequence files
        for f in self.generated_files:
            if '/virtual_sequences/' in str(f) or '\\virtual_sequences\\' in str(f):
                lines.append(str(f))
        
        lines.append("")
        lines.append("# Generated Test Files")
        lines.append(f"+incdir+{output_dir}/tests")
        
        # Add generated test files
        for f in self.generated_files:
            if '/tests/' in str(f) or '\\tests\\' in str(f):
                lines.append(str(f))
        
        lines.append("")
        lines.append("# Package and Testbench")
        lines.append(f"{output_dir}/{self.short_name}_pkg.sv")
        lines.append(f"{output_dir}/{self.short_name}_tb.sv")
        
        output_path = output_dir / output_filename
        output_path.write_text('\n'.join(lines))
        self.output_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")
    
    def _generate_testbench_template(self, output_dir: Path, context: str, example: Optional[str]):
        """Generate a testbench template."""
        console.print("  [C.3] Generating Testbench Template...", end=" ")
        
        output_filename = f"{self.short_name}_tb.sv"
        
        # Build interface instances
        interface_instances = []
        for name, info in self.uvc_mapping.get('uvcs', {}).items():
            kind = info.get('kind', '')
            # Convert env kind to interface kind
            if_kind = kind.replace('_env', '_if')
            interface_instances.append(f"- {if_kind} {name.replace('_env', '_if')}_inst")
        
        # Build DUT connections placeholder
        dut_connections = f"""Connect signals according to {self.block_name} port list:
- Clock and reset
- Feature buffer interface signals
- Kernel memory interface signals
- Output buffer interface signals
- PSIN/ADDIN interface signals
- Register interface signals (decoded to control signals)
- Status signals"""
        
        prompt = format_prompt(
            TESTBENCH_PROMPT,
            block_name=self.block_name,
            interface_instances='\n'.join(interface_instances),
            dut_connections=dut_connections,
            output_filename=output_filename
        )
        
        examples = [example] if example else None
        response = self.llm.generate(prompt, context=context, examples=examples)
        
        code = extract_code_from_response(response.content)
        output_path = output_dir / output_filename
        output_path.write_text(code)
        self.output_files.append(output_path)
        
        console.print(f"[green]OK[/green] ({output_filename})")
    
    def _get_ordered_file_list(self) -> List[str]:
        """Get ordered list of files for inclusion in package."""
        # Order: interfaces, sequence items, sequences, sequencers, drivers, monitors, agents, envs, scoreboards, vseqs, tests
        ordered = []
        
        # Group files by type
        ip_files = [f for f in self.generated_files if '/ip/' in str(f) or '\\ip\\' in str(f)]
        vseq_files = [f for f in self.generated_files if '/virtual_sequences/' in str(f) or '\\virtual_sequences\\' in str(f)]
        test_files = [f for f in self.generated_files if '/tests/' in str(f) or '\\tests\\' in str(f)]
        
        # Add IP files in dependency order
        for pattern in ['_if.sv', '_virtual_sequencer.sv', '_scoreboard.sv', '_env.sv']:
            for f in ip_files:
                if f.name.endswith(pattern.replace('.sv', '.sv')):
                    ordered.append(f.name)
        
        # Add virtual sequence files FIRST (tests depend on vseq classes)
        for f in vseq_files:
            if '_vseq.sv' in f.name:
                ordered.append(f.name)
        
        # Add test files AFTER vseq files
        for f in test_files:
            if '_test.sv' in f.name:
                ordered.append(f.name)
        
        return ordered


def run_phase_c(
    config: Config,
    llm: UVMGeneratorLLM,
    block_config: Dict,
    uvc_mapping: Dict,
    generated_files: List[Path]
) -> List[Path]:
    """Convenience function to run Phase C."""
    phase = PhaseCPackage(config, llm, block_config, uvc_mapping, generated_files)
    return phase.run()
