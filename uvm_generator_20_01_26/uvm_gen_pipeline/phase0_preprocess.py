"""
Phase 0: Preprocessing
Parses input files and generates configuration for subsequent phases.
"""

import yaml
from pathlib import Path
from dataclasses import asdict
from typing import Dict, Any, Tuple
from rich.console import Console
from rich.panel import Panel

from config import Config
from parsers import (
    parse_block_yaml,
    parse_vplan_yaml,
    parse_model_cpp,
    generate_uvc_mapping,
    BlockConfig,
    TestCase,
    ModelInfo
)

console = Console()


class Phase0Preprocessor:
    """Handles all preprocessing tasks before code generation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.block_config: BlockConfig = None
        self.test_cases: list[TestCase] = []
        self.model_info: ModelInfo = None
        self.uvc_mapping: Dict[str, Any] = {}
        
    def run(self) -> Tuple[Dict, list, Dict, Dict]:
        """
        Execute Phase 0 preprocessing.
        
        Returns:
            Tuple of (block_config_dict, test_cases, model_info_dict, uvc_mapping)
        """
        console.print(Panel("[bold cyan]Phase 0: Preprocessing[/bold cyan]"))
        
        # Step 0.1: Parse Block YAML
        self._parse_block_yaml()
        
        # Step 0.2: Parse Vplan YAML
        self._parse_vplan()
        
        # Step 0.3: Parse C++ Model
        self._parse_model()
        
        # Step 0.4: Generate UVC Mapping
        self._generate_uvc_mapping()
        
        # Step 0.5: Save intermediate configs
        self._save_configs()
        
        console.print("[green]Phase 0 complete[/green]\n")
        
        return (
            asdict(self.block_config),
            self.test_cases,
            asdict(self.model_info) if self.model_info else {},
            self.uvc_mapping
        )
    
    def _parse_block_yaml(self):
        """Parse the block YAML configuration file."""
        console.print("  [0.1] Parsing Block YAML...", end=" ")
        
        block_file = self.config.pipeline.block_yaml_file
        if not block_file.exists():
            # Try in golden reference path
            block_file = self.config.pipeline.golden_ref_path / "model_files" / block_file.name
        
        if not block_file.exists():
            raise FileNotFoundError(f"Block YAML file not found: {block_file}")
        
        self.block_config = parse_block_yaml(block_file)
        console.print(f"[green]OK[/green] ({self.block_config.name})")
        
        if self.config.pipeline.verbose:
            console.print(f"    - Found {len(self.block_config.interfaces)} interfaces")
    
    def _parse_vplan(self):
        """Parse the verification plan YAML file."""
        console.print("  [0.2] Parsing Vplan YAML...", end=" ")
        
        vplan_file = self.config.pipeline.vplan_file
        if not vplan_file.exists():
            vplan_file = self.config.pipeline.golden_ref_path / "model_files" / vplan_file.name
        
        if not vplan_file.exists():
            raise FileNotFoundError(f"Vplan file not found: {vplan_file}")
        
        self.test_cases = parse_vplan_yaml(vplan_file)
        console.print(f"[green]OK[/green] ({len(self.test_cases)} test cases)")
        
        if self.config.pipeline.verbose:
            for tc in self.test_cases:
                console.print(f"    - {tc.tc_id}")
    
    def _parse_model(self):
        """Parse the C++ reference model."""
        console.print("  [0.3] Parsing C++ Model...", end=" ")
        
        model_file = self.config.pipeline.model_cpp_file
        if not model_file.exists():
            model_file = self.config.pipeline.golden_ref_path / "model_files" / model_file.name
        
        if not model_file.exists():
            console.print("[yellow]SKIP - Not found (optional)[/yellow]")
            return
        
        self.model_info = parse_model_cpp(model_file)
        console.print(f"[green]OK[/green] ({self.model_info.num_args} args)")
        
        if self.config.pipeline.verbose:
            console.print(f"    - Input files: {self.model_info.input_files}")
            console.print(f"    - Parameters: {self.model_info.parameters}")
    
    def _generate_uvc_mapping(self):
        """Generate UVC mapping from block configuration."""
        console.print("  [0.4] Generating UVC Mapping...", end=" ")
        
        self.uvc_mapping = generate_uvc_mapping(self.block_config)
        console.print(f"[green]OK[/green] ({len(self.uvc_mapping.get('uvcs', {}))} UVCs)")
    
    def _save_configs(self):
        """Save intermediate configuration files."""
        console.print("  [0.5] Saving configurations...", end=" ")
        
        output_dir = self.config.pipeline.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save UVC mapping
        uvc_mapping_file = output_dir / "uvc_mapping.yaml"
        with open(uvc_mapping_file, 'w') as f:
            yaml.dump(self.uvc_mapping, f, default_flow_style=False)
        
        # Save model details
        if self.model_info:
            model_details_file = output_dir / "model_details.txt"
            with open(model_details_file, 'w') as f:
                f.write(f"Number of arguments: {self.model_info.num_args}\n")
                f.write(f"Argument names: {', '.join(self.model_info.arg_names)}\n")
                f.write(f"Input files: {', '.join(self.model_info.input_files)}\n")
                f.write(f"Output files: {', '.join(self.model_info.output_files)}\n")
                f.write(f"Parameters: {', '.join(self.model_info.parameters)}\n")
        
        console.print("[green]OK[/green]")


def run_phase0(config: Config) -> Tuple[Dict, list, Dict, Dict]:
    """Convenience function to run Phase 0."""
    preprocessor = Phase0Preprocessor(config)
    return preprocessor.run()
