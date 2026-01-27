#!/usr/bin/env python3
"""
UVM Test Case Generator - Main Orchestrator

A model-agnostic pipeline for generating UVM test cases for any IP block.
Uses OpenAI LLM for intelligent code generation with few-shot learning.

Usage:
    python main.py --vplan Vplan.yaml --block Block_YAML_file.txt --model model.cpp --output ./generated

Environment Variables:
    OPENAI_API_KEY: Your OpenAI API key (required)
    OPENAI_MODEL: Model to use (default: gpt-4-turbo-preview)
"""

import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure console for Windows compatibility
console = Console(force_terminal=True, legacy_windows=True)

from config import load_config, Config
from llm_client import UVMGeneratorLLM
from phase0_preprocess import run_phase0
from phase_a_infrastructure import run_phase_a
from phase_b_testgen import run_phase_b
from phase_c_package import run_phase_c


def print_banner():
    """Print the application banner."""
    banner = """
================================================================
           UVM Test Case Generator Pipeline                   
              Powered by OpenAI LLM                           
================================================================
    """
    console.print(banner, style="bold cyan")


def print_summary(config: Config, generated_files: list):
    """Print generation summary."""
    table = Table(title="Generation Summary", show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    
    ip_files = [f for f in generated_files if '/ip/' in str(f) or '\\ip\\' in str(f)]
    test_files = [f for f in generated_files if '/tests/' in str(f) or '\\tests\\' in str(f)]
    vseq_files = [f for f in generated_files if '/virtual_sequences/' in str(f) or '\\virtual_sequences\\' in str(f)]
    other_files = [f for f in generated_files if f not in ip_files and f not in test_files and f not in vseq_files]
    
    table.add_row("IP Infrastructure Files", str(len(ip_files)))
    table.add_row("Test Files (_test.sv)", str(len(test_files)))
    table.add_row("Virtual Sequences (_vseq.sv)", str(len(vseq_files)))
    table.add_row("Integration Files", str(len(other_files)))
    table.add_row("Total Files", str(len(generated_files)))
    
    console.print(table)
    console.print(f"\n[bold green]All files generated in: {config.pipeline.output_dir}[/bold green]")


class UVMGeneratorPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm: Optional[UVMGeneratorLLM] = None
        self.all_generated_files = []
        
    def initialize(self):
        """Initialize the pipeline components."""
        # Validate config
        self.config.validate()
        
        # Initialize LLM client
        self.llm = UVMGeneratorLLM(self.config.openai)
        
        # Create output directory
        self.config.pipeline.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self) -> list:
        """
        Execute the full pipeline.
        
        Returns:
            List of all generated file paths
        """
        start_time = datetime.now()
        
        console.print(f"[dim]Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")
        
        # Phase 0: Preprocessing
        block_config, test_cases, model_info, uvc_mapping = run_phase0(self.config)
        
        # Phase A: IP Infrastructure
        ip_files = run_phase_a(
            self.config,
            self.llm,
            block_config,
            uvc_mapping,
            model_info
        )
        self.all_generated_files.extend(ip_files)
        
        # Phase B: Test Case Generation
        # Pass infrastructure files from Phase A as context for better test generation
        test_files = run_phase_b(
            self.config,
            self.llm,
            block_config,
            test_cases,
            uvc_mapping,
            model_info,
            infra_files=ip_files  # Pass Phase A files as context
        )
        self.all_generated_files.extend(test_files)
        
        # Phase C: Package & Integration
        pkg_files = run_phase_c(
            self.config,
            self.llm,
            block_config,
            uvc_mapping,
            self.all_generated_files
        )
        self.all_generated_files.extend(pkg_files)
        
        # Print summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        console.print(f"\n[dim]Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        console.print(f"[dim]Duration: {duration.total_seconds():.1f} seconds[/dim]\n")
        
        print_summary(self.config, self.all_generated_files)
        
        return self.all_generated_files


@click.command()
@click.option(
    '--vplan', '-v',
    type=click.Path(exists=False),
    default='Vplan.yaml',
    help='Path to Vplan YAML file'
)
@click.option(
    '--block', '-b',
    type=click.Path(exists=False),
    default='Block_YAML_file.txt',
    help='Path to Block YAML file'
)
@click.option(
    '--model', '-m',
    type=click.Path(exists=False),
    default='psout_ac_fixed_14_11_25.cpp',
    help='Path to C++ reference model'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default='./generated',
    help='Output directory for generated files'
)
@click.option(
    '--uvc-path', '-u',
    type=click.Path(exists=False),
    default='../uvc',
    help='Path to UVC library'
)
@click.option(
    '--golden-ref', '-g',
    type=click.Path(exists=False),
    default='../Golden_reference_files',
    help='Path to golden reference files'
)
@click.option(
    '--no-scoreboard',
    is_flag=True,
    help='Skip scoreboard generation'
)
@click.option(
    '--no-package',
    is_flag=True,
    help='Skip package file generation'
)
@click.option(
    '--verbose',
    is_flag=True,
    default=True,
    help='Enable verbose output'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Parse inputs only, do not generate files'
)
def main(
    vplan: str,
    block: str,
    model: str,
    output: str,
    uvc_path: str,
    golden_ref: str,
    no_scoreboard: bool,
    no_package: bool,
    verbose: bool,
    dry_run: bool
):
    """
    UVM Test Case Generator Pipeline
    
    Generates complete UVM testbench from Vplan, Block YAML, and C++ model.
    
    Requires OPENAI_API_KEY environment variable to be set.
    """
    print_banner()
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        console.print("[red]Error: OPENAI_API_KEY environment variable not set![/red]")
        console.print("\nPlease set your OpenAI API key:")
        console.print("  export OPENAI_API_KEY='your-api-key-here'")
        console.print("\nOr create a .env file with:")
        console.print("  OPENAI_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Load configuration
    config = load_config(
        vplan_file=vplan,
        block_yaml_file=block,
        model_cpp_file=model,
        output_dir=output,
        uvc_path=uvc_path,
        golden_ref_path=golden_ref
    )
    
    # Apply option flags
    config.pipeline.generate_scoreboard = not no_scoreboard
    config.pipeline.generate_package = not no_package
    config.pipeline.verbose = verbose
    
    # Show configuration
    if verbose:
        console.print(Panel(
            f"""[bold]Configuration:[/bold]
  Vplan:      {config.pipeline.vplan_file}
  Block YAML: {config.pipeline.block_yaml_file}
  Model:      {config.pipeline.model_cpp_file}
  Output:     {config.pipeline.output_dir}
  UVC Path:   {config.pipeline.uvc_library_path}
  Golden Ref: {config.pipeline.golden_ref_path}
  Model:      {config.openai.model}""",
            title="Settings",
            border_style="blue"
        ))
    
    if dry_run:
        console.print("\n[yellow]Dry run mode - only parsing inputs[/yellow]\n")
        # Just run Phase 0
        block_config, test_cases, model_info, uvc_mapping = run_phase0(config)
        console.print("[green]Dry run complete[/green]")
        return
    
    # Run the pipeline
    try:
        pipeline = UVMGeneratorPipeline(config)
        pipeline.initialize()
        generated_files = pipeline.run()
        
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
