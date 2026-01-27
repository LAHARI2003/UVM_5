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


def generate_uvc_mapping(block_config: BlockConfig, uvc_library_path: Path = None) -> Dict[str, Any]:
    """
    Generate UVC mapping configuration from block config.
    Maps interfaces to their UVC types and parameters.
    
    If uvc_library_path is provided, dynamically scans the UVC library
    to discover available sequences, parameters, and capabilities.
    """
    mapping = {
        "block_name": block_config.name,
        "uvcs": {}
    }
    
    # Alias mapping for legacy/alternative UVC names
    # Maps legacy names in Block YAML to actual UVC names in the library
    UVC_ALIASES = {
        "regbank_uvc": "register_uvc",
        "regbank_env": "register_env",
        "computation_uvc": "register_uvc",
        "computation_env": "register_env",
    }
    
    # Scan UVC library if path is provided
    uvc_library_info = {}
    if uvc_library_path and uvc_library_path.exists():
        uvc_library_info = scan_uvc_library(uvc_library_path)
    
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
            
            # Resolve aliases (e.g., regbank_uvc -> register_uvc)
            resolved_uvc_type = UVC_ALIASES.get(uvc_type, uvc_type)
            resolved_base_type = UVC_ALIASES.get(base_type, base_type)
            
            # Get sequencer type and sequences from library scan or fallback
            sequencer_type = resolved_base_type.replace('_env', '_sequencer')
            sequence_types = get_sequence_types(resolved_base_type)
            interface_type = None
            package_name = None
            
            # Override with dynamically scanned info if available
            if resolved_uvc_type in uvc_library_info:
                lib_info = uvc_library_info[resolved_uvc_type]
                sequencer_type = lib_info.get('sequencer_type', sequencer_type)
                sequence_types = lib_info.get('sequences', sequence_types)
                interface_type = lib_info.get('interface_type')
                package_name = lib_info.get('package_name')
            
            mapping["uvcs"][interface.name] = {
                "type": resolved_uvc_type,
                "kind": kind,
                "params": interface.params,
                "model_arg": interface.map_to_model,
                "sequencer_type": sequencer_type,
                "sequence_types": sequence_types,
                "interface_type": interface_type,
                "package_name": package_name,
                "param_signature": get_param_signature(resolved_base_type, uvc_library_info.get(resolved_uvc_type, {}))
            }
    
    return mapping


def scan_uvc_library(uvc_path: Path) -> Dict[str, Dict]:
    """
    Scan UVC library directory to discover available UVCs and their components.
    
    This function dynamically parses through all UVCs in the library to extract:
    - Available sequences and their parameters
    - Sequencer types and their parameter signatures
    - Interface types
    - Package information
    
    Returns:
        Dictionary mapping UVC names to their discovered information
    """
    uvc_info = {}
    
    if not uvc_path.exists():
        return uvc_info
    
    # Find all UVC directories
    for uvc_dir in uvc_path.iterdir():
        if not uvc_dir.is_dir():
            continue
        
        uvc_name = uvc_dir.name  # e.g., "istream_uvc"
        
        info = {
            "path": str(uvc_dir),
            "sequences": [],
            "sequencer_type": None,
            "env_type": None,
            "interface_type": None,
            "package_name": None,
            "parameters": [],
            "param_defaults": {}
        }
        
        # Parse package file to get all components
        pkg_dir = uvc_dir / "pkg"
        if pkg_dir.exists():
            info.update(_parse_uvc_package(pkg_dir))
        
        # Parse env file to get parameter signature
        env_dir = uvc_dir / "env"
        if env_dir.exists():
            info.update(_parse_uvc_env(env_dir))
        
        # Parse sequencer file to get sequencer details
        seqr_dir = uvc_dir / "sequencer"
        if seqr_dir.exists():
            info.update(_parse_uvc_sequencer(seqr_dir))
        
        # Parse sequences directory to get available sequences
        seq_dir = uvc_dir / "sequences"
        if seq_dir.exists():
            info["sequences"] = _parse_uvc_sequences(seq_dir)
        
        # Parse interface file
        if_dir = uvc_dir / "interface"
        if if_dir.exists():
            info.update(_parse_uvc_interface(if_dir))
        
        uvc_info[uvc_name] = info
    
    return uvc_info


def _parse_uvc_package(pkg_dir: Path) -> Dict:
    """Parse UVC package file to extract package name and included components."""
    result = {}
    
    for pkg_file in pkg_dir.glob("*.sv"):
        content = pkg_file.read_text()
        
        # Extract package name
        pkg_match = re.search(r'package\s+(\w+)\s*;', content)
        if pkg_match:
            result["package_name"] = pkg_match.group(1)
        
        # Extract included files to understand component structure
        includes = re.findall(r'`include\s+"([^"]+)"', content)
        result["package_includes"] = includes
        
    return result


def _parse_uvc_env(env_dir: Path) -> Dict:
    """Parse UVC env file to extract environment class and parameters."""
    result = {}
    
    for env_file in env_dir.glob("*.sv"):
        content = env_file.read_text()
        
        # Extract class definition with parameters
        # e.g., "class istream_env #(int DATA_WIDTH = 32) extends uvm_env"
        class_match = re.search(
            r'class\s+(\w+)\s*(?:#\s*\(\s*([^)]+)\s*\))?\s*extends\s+(\w+)',
            content
        )
        if class_match:
            result["env_type"] = class_match.group(1)
            params_str = class_match.group(2)
            result["base_class"] = class_match.group(3)
            
            if params_str:
                result["parameters"], result["param_defaults"] = _parse_param_list(params_str)
    
    return result


def _parse_uvc_sequencer(seqr_dir: Path) -> Dict:
    """Parse UVC sequencer file to extract sequencer type and parameters."""
    result = {}
    
    for seqr_file in seqr_dir.glob("*.sv"):
        content = seqr_file.read_text()
        
        # Extract class definition with parameters
        class_match = re.search(
            r'class\s+(\w+)\s*(?:#\s*\(\s*([^)]+)\s*\))?\s*extends\s+(\w+)',
            content
        )
        if class_match:
            result["sequencer_type"] = class_match.group(1)
            params_str = class_match.group(2)
            
            if params_str and "parameters" not in result:
                result["parameters"], result["param_defaults"] = _parse_param_list(params_str)
    
    return result


def _parse_uvc_sequences(seq_dir: Path) -> List[Dict]:
    """Parse UVC sequences directory to extract all available sequences."""
    sequences = []
    
    for seq_file in seq_dir.glob("*.sv"):
        content = seq_file.read_text()
        
        # Extract sequence class definitions
        # e.g., "class istream_directed_write_sequence #(int DATA_WIDTH = 32) extends uvm_sequence"
        class_matches = re.finditer(
            r'class\s+(\w+)\s*(?:#\s*\(\s*([^)]+)\s*\))?\s*extends\s+(uvm_sequence|uvm_sequence\s*#\([^)]+\))',
            content
        )
        
        for match in class_matches:
            seq_name = match.group(1)
            params_str = match.group(2)
            
            seq_info = {
                "name": seq_name,
                "file": seq_file.name,
                "parameters": [],
                "param_defaults": {},
                "operation_type": _infer_operation_type(seq_name)
            }
            
            if params_str:
                seq_info["parameters"], seq_info["param_defaults"] = _parse_param_list(params_str)
            
            # Try to extract additional properties from the sequence
            seq_info.update(_analyze_sequence_body(content, seq_name))
            
            sequences.append(seq_info)
    
    return sequences


def _parse_uvc_interface(if_dir: Path) -> Dict:
    """Parse UVC interface file to extract interface type and signals."""
    result = {}
    
    for if_file in if_dir.glob("*.sv"):
        content = if_file.read_text()
        
        # Extract interface definition with parameters
        if_match = re.search(
            r'interface\s+(\w+)\s*(?:#\s*\(\s*([^)]+)\s*\))?',
            content
        )
        if if_match:
            result["interface_type"] = if_match.group(1)
    
    return result


def _parse_param_list(params_str: str) -> tuple:
    """Parse parameter list string and extract parameter names and defaults."""
    parameters = []
    param_defaults = {}
    
    # Split by comma, handling nested parentheses
    params = re.findall(r'(?:int|parameter\s+int|parameter)\s+(\w+)\s*(?:=\s*(\d+))?', params_str)
    
    for param_name, default_val in params:
        parameters.append(param_name)
        if default_val:
            param_defaults[param_name] = int(default_val)
    
    return parameters, param_defaults


def _infer_operation_type(seq_name: str) -> str:
    """Infer the operation type from sequence name."""
    name_lower = seq_name.lower()
    
    if 'write' in name_lower:
        if 'read' in name_lower:
            return 'read_write'
        return 'write'
    elif 'read' in name_lower:
        return 'read'
    elif 'configure' in name_lower:
        return 'configure'
    elif 'random' in name_lower:
        return 'random'
    elif 'burst' in name_lower:
        return 'burst'
    else:
        return 'generic'


def _analyze_sequence_body(content: str, seq_name: str) -> Dict:
    """Analyze sequence body to extract additional properties."""
    result = {}
    
    # Check if sequence reads from file
    if '$readmemh' in content or '$readmemb' in content:
        result["uses_file_input"] = True
        
        # Try to extract file path variable
        file_var_match = re.search(r'string\s+(\w*file\w*)', content, re.IGNORECASE)
        if file_var_match:
            result["file_path_var"] = file_var_match.group(1)
    
    # Check if sequence uses size parameter
    if re.search(r'int\s+size\s*;', content):
        result["has_size_param"] = True
    
    # Check if it's directed or random
    if 'randomize' in content:
        result["is_randomized"] = True
    else:
        result["is_randomized"] = False
    
    return result


def get_param_signature(base_type: str, lib_info: Dict) -> str:
    """Generate parameter signature string for a UVC type."""
    params = lib_info.get('parameters', [])
    defaults = lib_info.get('param_defaults', {})
    
    if not params:
        return ""
    
    parts = []
    for param in params:
        if param in defaults:
            parts.append(f"int {param} = {defaults[param]}")
        else:
            parts.append(f"int {param}")
    
    return f"#({', '.join(parts)})"


def get_sequence_types(base_type: str) -> List[str]:
    """Get available sequence types for a UVC base type (fallback for when library scan is not available)."""
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
