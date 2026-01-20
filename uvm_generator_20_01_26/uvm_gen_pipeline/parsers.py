"""
Parser module for UVM Generator inputs.
Handles parsing of Block YAML, Vplan YAML, and C++ model files.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Interface:
    """Represents a DUT interface."""
    name: str
    kind: str  # e.g., "istream_env#(64)", "dpmem_env#(64,9)"
    params: Dict[str, Any] = field(default_factory=dict)
    map_to_model: str = ""  # e.g., "arg : feature"


@dataclass
class BlockConfig:
    """Parsed Block YAML configuration."""
    name: str
    clock_name: str
    clock_freq: str
    reset_name: str
    reset_active_low: bool
    model_language: str
    model_entry: str
    model_lib_path: str
    interfaces: List[Interface] = field(default_factory=list)


@dataclass
class StimulusConfig:
    """Stimulus generation configuration from Vplan."""
    regbank_program: Dict[str, Any] = field(default_factory=dict)
    input_provisioning: Dict[str, Any] = field(default_factory=dict)
    trigger_compute: Dict[str, Any] = field(default_factory=dict)
    output_read: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """Represents a test case from Vplan."""
    tc_id: str
    active_uvcs: List[str]
    stimulus: StimulusConfig
    observability: List[str] = field(default_factory=list)
    coverage_intent: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ModelInfo:
    """Parsed C++ model information."""
    num_args: int
    arg_names: List[str]
    input_files: List[str]
    output_files: List[str]
    parameters: List[str]
    usage_string: str


def parse_block_yaml(file_path: Path) -> BlockConfig:
    """
    Parse the Block YAML file.
    
    Handles the semi-structured text format used in Block_YAML_file.txt
    """
    content = file_path.read_text()
    
    # Initialize defaults
    config = BlockConfig(
        name="",
        clock_name="clk",
        clock_freq="100MHz",
        reset_name="resetn",
        reset_active_low=True,
        model_language="Cmodel",
        model_entry="main",
        model_lib_path="",
        interfaces=[]
    )
    
    lines = content.split('\n')
    current_interface = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Parse block name
        if line.startswith("Name :") and config.name == "":
            config.name = line.split(":", 1)[1].strip()
        
        # Parse clock
        elif line.lower().startswith("name : clk") or (line.startswith("name :") and "clk" in line.lower()):
            config.clock_name = line.split(":", 1)[1].strip()
        
        # Parse frequency
        elif line.lower().startswith("frequency"):
            config.clock_freq = line.split(":", 1)[1].strip()
        
        # Parse reset
        elif "resetn" in line.lower() or "reset" in line.lower():
            if "name" in line.lower():
                config.reset_name = line.split(":", 1)[1].strip()
        
        # Parse active low
        elif "active_low" in line.lower():
            config.reset_active_low = "true" in line.lower()
        
        # Parse model info
        elif line.lower().startswith("language"):
            config.model_language = line.split(":", 1)[1].strip()
        elif line.lower().startswith("entry"):
            config.model_entry = line.split(":", 1)[1].strip()
        elif line.lower().startswith("lib_path"):
            config.model_lib_path = line.split(":", 1)[1].strip()
        
        # Parse interfaces
        elif line.startswith("Name : m_") or line.startswith("Name :m_"):
            # Save previous interface if exists
            if current_interface:
                config.interfaces.append(current_interface)
            
            name = line.split(":", 1)[1].strip()
            current_interface = Interface(name=name, kind="", params={})
        
        elif line.startswith("Kind :") and current_interface:
            current_interface.kind = line.split(":", 1)[1].strip()
        
        elif line.startswith("params :") and current_interface:
            # Parse params like { DATA_WIDTH : 64 }
            params_str = line.split(":", 1)[1].strip()
            params_match = re.findall(r'(\w+)\s*:\s*(\d+)', params_str)
            current_interface.params = {k: int(v) for k, v in params_match}
        
        elif line.startswith("Map_to_model :") and current_interface:
            current_interface.map_to_model = line.split(":", 1)[1].strip()
        
        i += 1
    
    # Don't forget last interface
    if current_interface:
        config.interfaces.append(current_interface)
    
    return config


def parse_vplan_yaml(file_path: Path) -> List[TestCase]:
    """Parse the Vplan YAML file."""
    content = file_path.read_text()
    data = yaml.safe_load(content)
    
    test_cases = []
    
    # Handle both list and single test case format
    if isinstance(data, list):
        items = data
    else:
        items = [data]
    
    for item in items:
        if not item:
            continue
            
        # Parse stimulus generation
        stimulus = StimulusConfig()
        stim_data = item.get('Stimulus_Generation', [])
        
        for stim_item in stim_data:
            if isinstance(stim_item, dict):
                if 'regbank_program' in stim_item:
                    stimulus.regbank_program = stim_item['regbank_program']
                if 'input_provisioning' in stim_item:
                    stimulus.input_provisioning = stim_item['input_provisioning']
                if 'trigger_compute' in stim_item:
                    stimulus.trigger_compute = stim_item['trigger_compute']
                if 'output_read' in stim_item:
                    stimulus.output_read = stim_item['output_read']
        
        # Parse coverage intent
        coverage = {}
        cov_data = item.get('Coverage_Intent', [])
        for cov_item in cov_data:
            if isinstance(cov_item, dict):
                coverage.update(cov_item)
        
        test_case = TestCase(
            tc_id=item.get('TC_ID', 'UNKNOWN'),
            active_uvcs=item.get('Active_UVCs', []),
            stimulus=stimulus,
            observability=item.get('Observability', []),
            coverage_intent=coverage
        )
        test_cases.append(test_case)
    
    return test_cases


def parse_model_cpp(file_path: Path) -> ModelInfo:
    """
    Parse the C++ model file to extract argument information.
    
    Extracts:
    - Number of arguments from argc check
    - Argument names from usage string
    - Input/output file mappings
    - Parameters
    """
    content = file_path.read_text()
    
    model_info = ModelInfo(
        num_args=0,
        arg_names=[],
        input_files=[],
        output_files=[],
        parameters=[],
        usage_string=""
    )
    
    # Find argc check (e.g., "if (argc != 11)")
    argc_match = re.search(r'argc\s*!=\s*(\d+)', content)
    if argc_match:
        model_info.num_args = int(argc_match.group(1)) - 1  # Subtract 1 for program name
    
    # Find usage string
    usage_match = re.search(r'Usage:\s*%s\s+([^"\\]+)', content)
    if usage_match:
        model_info.usage_string = usage_match.group(1).strip()
        # Parse argument names from usage
        args = model_info.usage_string.split()
        model_info.arg_names = args
    
    # Parse argv assignments to identify argument purposes
    # Look for patterns like: const char *kernel_file = argv[1];
    argv_pattern = re.compile(r'(?:const\s+)?(?:char\s*\*|std::string)\s+(\w+)\s*=\s*argv\[(\d+)\]')
    for match in argv_pattern.finditer(content):
        var_name = match.group(1)
        arg_index = int(match.group(2))
        
        if 'file' in var_name.lower():
            if 'output' in var_name.lower() or 'out' in var_name.lower():
                model_info.output_files.append(var_name)
            else:
                model_info.input_files.append(var_name)
        else:
            model_info.parameters.append(var_name)
    
    # Also look for common parameter patterns
    param_patterns = ['mode', 'sign_8b', 'PS_FIRST', 'PS_MODE', 'PS_LAST']
    for param in param_patterns:
        if param not in model_info.parameters and param.lower() in content.lower():
            model_info.parameters.append(param)
    
    return model_info


def generate_uvc_mapping(block_config: BlockConfig) -> Dict[str, Any]:
    """
    Generate UVC mapping configuration from block config.
    Maps interfaces to their UVC types and parameters.
    """
    mapping = {
        "block_name": block_config.name,
        "uvcs": {}
    }
    
    for interface in block_config.interfaces:
        # Parse the kind to extract base type and parameters
        kind = interface.kind
        
        # Extract base UVC type (e.g., "istream_env" from "istream_env#(64)")
        base_match = re.match(r'(\w+)(?:#\(([^)]+)\))?', kind)
        if base_match:
            base_type = base_match.group(1)
            params_str = base_match.group(2) or ""
            
            # Map to UVC library path
            uvc_type = base_type.replace('_env', '_uvc')
            
            mapping["uvcs"][interface.name] = {
                "type": uvc_type,
                "kind": kind,
                "params": interface.params,
                "model_arg": interface.map_to_model,
                "sequencer_type": base_type.replace('_env', '_sequencer'),
                "sequence_types": get_sequence_types(base_type)
            }
    
    return mapping


def get_sequence_types(base_type: str) -> List[str]:
    """Get available sequence types for a UVC base type."""
    sequence_map = {
        "istream_env": [
            "istream_directed_write_sequence",
            "istream_directed_random_burst_write_sequence"
        ],
        "ostream_env": [
            "ostream_random_burst_read_sequence",
            "ostream_directed_read_sequence"
        ],
        "dpmem_env": [
            "dpmem_directed_write_sequence",
            "dpmem_directed_read_sequence"
        ],
        "spmem_env": [
            "spmem_directed_write_sequence",
            "spmem_directed_read_sequence"
        ],
        "register_env": [
            "register_configure_write_seq",
            "register_write_sequence"
        ],
        "regbank_env": [
            "register_configure_write_seq",
            "register_write_sequence"
        ]
    }
    return sequence_map.get(base_type, [])
