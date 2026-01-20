"""
Configuration module for UVM Test Case Generator.
Handles environment variables and global settings.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1"))
    temperature: float = 0.2
    max_tokens: int = 4096
    org_id: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_ORG_ID"))


@dataclass
class PipelineConfig:
    """Pipeline configuration settings."""
    # Input paths
    vplan_file: Path = Path("Vplan.yaml")
    block_yaml_file: Path = Path("Block_YAML_file.txt")
    model_cpp_file: Path = Path("model.cpp")
    
    # Reference paths
    uvc_library_path: Path = Path("../uvc")
    golden_ref_path: Path = Path("../Golden_reference_files")
    
    # Output paths
    output_dir: Path = Path("./generated")
    
    # Generation options
    generate_scoreboard: bool = True
    generate_package: bool = True
    verbose: bool = True


@dataclass
class Config:
    """Main configuration container."""
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return True


def load_config(
    vplan_file: Optional[str] = None,
    block_yaml_file: Optional[str] = None,
    model_cpp_file: Optional[str] = None,
    output_dir: Optional[str] = None,
    uvc_path: Optional[str] = None,
    golden_ref_path: Optional[str] = None,
) -> Config:
    """Load configuration with optional overrides."""
    config = Config()
    
    if vplan_file:
        config.pipeline.vplan_file = Path(vplan_file)
    if block_yaml_file:
        config.pipeline.block_yaml_file = Path(block_yaml_file)
    if model_cpp_file:
        config.pipeline.model_cpp_file = Path(model_cpp_file)
    if output_dir:
        config.pipeline.output_dir = Path(output_dir)
    if uvc_path:
        config.pipeline.uvc_library_path = Path(uvc_path)
    if golden_ref_path:
        config.pipeline.golden_ref_path = Path(golden_ref_path)
    
    return config
