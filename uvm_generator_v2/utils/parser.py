"""
YAML Parsers for Block and Vplan files - V2 (Generic/Flexible)

Key Improvements:
- Supports both standard YAML and legacy custom formats
- Auto-detects format and parses accordingly
- Generic parameter extraction (not hardcoded to mode/sign_8b)
- Better error handling with informative messages
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class BlockYAMLParser:
    """
    Parser for Block YAML file (IP description)
    
    Supports two formats:
    1. Standard YAML format (recommended for new IPs)
    2. Legacy custom format (for backward compatibility)
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Block YAML not found: {file_path}")
        
        self.raw_content = self.file_path.read_text(encoding='utf-8')
        self.data = self._parse()
        self._validate()
    
    def _detect_format(self) -> str:
        """Detect if file is standard YAML or legacy format"""
        # Check for legacy format markers FIRST (more specific)
        legacy_markers = ['Name :', 'Kind :', 'Block :', 'Clocks :', 'Resets :', 'Interfaces :']
        for marker in legacy_markers:
            if marker in self.raw_content:
                return 'legacy'
        
        # Also check without space before colon
        if 'Block:' in self.raw_content and 'Name :' in self.raw_content:
            return 'legacy'
        
        try:
            parsed = yaml.safe_load(self.raw_content)
            if isinstance(parsed, dict) and ('DUT' in parsed or 'dut' in parsed or 'block' in parsed):
                return 'standard'
        except yaml.YAMLError:
            pass
        
        return 'standard'  # Default to standard
    
    def _parse(self) -> Dict[str, Any]:
        """Parse the block YAML file (auto-detect format)"""
        format_type = self._detect_format()
        
        if format_type == 'standard':
            return self._parse_standard_yaml()
        else:
            return self._parse_legacy_format()
    
    def _parse_standard_yaml(self) -> Dict[str, Any]:
        """Parse standard YAML format"""
        raw_data = yaml.safe_load(self.raw_content)
        
        # Normalize keys (handle DUT, dut, block variations)
        dut_data = raw_data.get('DUT') or raw_data.get('dut') or raw_data.get('block', {})
        
        data = {
            'block_name': dut_data.get('module_name', dut_data.get('name', '')),
            'clock': self._normalize_clock(dut_data.get('clock', {})),
            'reset': self._normalize_reset(dut_data.get('reset', {})),
            'model': self._normalize_model(dut_data.get('reference_model', dut_data.get('model', {}))),
            'interfaces': self._normalize_interfaces(dut_data.get('interfaces', {})),
            'raw': raw_data  # Keep raw data for custom fields
        }
        
        return data
    
    def _normalize_clock(self, clock_data: Union[str, Dict]) -> Dict:
        """Normalize clock data to consistent format"""
        if isinstance(clock_data, str):
            return {'name': clock_data, 'frequency': ''}
        return {
            'name': clock_data.get('name', clock_data.get('signal', 'clk')),
            'frequency': clock_data.get('frequency', '')
        }
    
    def _normalize_reset(self, reset_data: Union[str, Dict]) -> Dict:
        """Normalize reset data to consistent format"""
        if isinstance(reset_data, str):
            return {'name': reset_data, 'active_low': 'n' in reset_data.lower()}
        return {
            'name': reset_data.get('name', reset_data.get('signal', 'resetn')),
            'active_low': reset_data.get('active_low', reset_data.get('polarity', 'active_low') == 'active_low')
        }
    
    def _normalize_model(self, model_data: Union[str, Dict]) -> Dict:
        """Normalize reference model data"""
        if isinstance(model_data, str):
            return {'type': 'C_model', 'path': model_data, 'executable': '', 'command_format': ''}
        return {
            'type': model_data.get('type', 'C_model'),
            'path': model_data.get('path', ''),
            'executable': model_data.get('executable', ''),
            'command_format': model_data.get('command_format', ''),
            'arguments': model_data.get('arguments', [])
        }
    
    def _normalize_interfaces(self, interfaces_data: Union[List, Dict]) -> List[Dict]:
        """Normalize interfaces to consistent list format"""
        interfaces = []
        
        if isinstance(interfaces_data, dict):
            # Dict format: {interface_name: {type: ..., parameters: ...}}
            for name, details in interfaces_data.items():
                if isinstance(details, dict):
                    interfaces.append({
                        'name': name,
                        'kind': details.get('type', details.get('kind', '')),
                        'params': self._extract_params(details.get('parameters', details.get('params', []))),
                        'virtual_if': details.get('virtual_if', ''),
                        'map_to_model': details.get('map_to_model', '')
                    })
        elif isinstance(interfaces_data, list):
            # List format: [{name: ..., type: ...}, ...]
            for item in interfaces_data:
                if isinstance(item, dict):
                    interfaces.append({
                        'name': item.get('name', ''),
                        'kind': item.get('type', item.get('kind', '')),
                        'params': self._extract_params(item.get('parameters', item.get('params', []))),
                        'virtual_if': item.get('virtual_if', ''),
                        'map_to_model': item.get('map_to_model', '')
                    })
        
        return interfaces
    
    def _extract_params(self, params: Union[List, Dict, str]) -> Dict:
        """Extract parameters to consistent dict format"""
        if isinstance(params, dict):
            return params
        elif isinstance(params, list):
            # [64, 9] -> {DATA_WIDTH: 64, ADDR_WIDTH: 9} or just store as list
            return {'values': params}
        elif isinstance(params, str):
            # Parse "{ DATA_WIDTH : 64 }" format
            matches = re.findall(r'(\w+)\s*:\s*(\w+)', params)
            return dict(matches)
        return {}
    
    def _parse_legacy_format(self) -> Dict[str, Any]:
        """Parse legacy custom format (backward compatibility)"""
        data = {
            'block_name': '',
            'clock': {'name': '', 'frequency': ''},
            'reset': {'name': '', 'active_low': False},
            'model': {'type': '', 'path': '', 'executable': ''},
            'interfaces': []
        }
        
        lines = self.raw_content.split('\n')
        current_section = None
        current_interface = None
        
        def normalize_key(s):
            """Normalize a key by removing spaces around colon"""
            return s.lower().replace(' ', '')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            line_lower = line_stripped.lower()
            line_normalized = normalize_key(line_stripped)
            
            # Section detection (handle "Block :", "Block:", "Block" variations)
            if line_normalized.startswith('block:') or line_stripped == 'Block' or line_stripped == 'Block :':
                current_section = 'block'
                continue
            elif line_normalized.startswith('clocks:') or line_stripped == 'Clocks' or line_stripped == 'Clocks :':
                current_section = 'clocks'
                continue
            elif line_normalized.startswith('resets:') or line_stripped == 'Resets' or line_stripped == 'Resets :':
                current_section = 'resets'
                continue
            elif line_normalized.startswith('interfaces:') or line_stripped == 'Interfaces' or line_stripped == 'Interfaces :':
                current_section = 'interfaces'
                continue
            elif line_normalized.startswith('model:') or line_normalized.startswith('reference_model:'):
                current_section = 'model'
                continue
            
            # Parse based on current section
            if current_section == 'block':
                if line_normalized.startswith('name:'):
                    data['block_name'] = line_stripped.split(':', 1)[1].strip()
            
            elif current_section == 'clocks':
                if line_normalized.startswith('name:'):
                    data['clock']['name'] = line_stripped.split(':', 1)[1].strip()
                elif line_normalized.startswith('frequency:'):
                    data['clock']['frequency'] = line_stripped.split(':', 1)[1].strip()
            
            elif current_section == 'resets':
                if line_normalized.startswith('name:'):
                    data['reset']['name'] = line_stripped.split(':', 1)[1].strip()
                elif line_normalized.startswith('active_low:'):
                    val = line_stripped.split(':', 1)[1].strip().lower()
                    data['reset']['active_low'] = val in ['true', 'yes', '1']
            
            elif current_section == 'model':
                if line_normalized.startswith('language:') or line_normalized.startswith('type:'):
                    data['model']['type'] = line_stripped.split(':', 1)[1].strip()
                elif line_normalized.startswith('entry:'):
                    data['model']['entry'] = line_stripped.split(':', 1)[1].strip()
                elif line_normalized.startswith('lib_path:') or line_normalized.startswith('executable:'):
                    data['model']['executable'] = line_stripped.split(':', 1)[1].strip()
                elif line_normalized.startswith('path:'):
                    data['model']['path'] = line_stripped.split(':', 1)[1].strip()
            
            elif current_section == 'interfaces':
                if line_normalized.startswith('name:'):
                    # Save previous interface if exists
                    if current_interface and current_interface.get('name'):
                        data['interfaces'].append(current_interface)
                    current_interface = {
                        'name': line_stripped.split(':', 1)[1].strip().lstrip('- '),
                        'kind': '',
                        'params': {},
                        'virtual_if': '',
                        'map_to_model': ''
                    }
                elif current_interface:
                    if line_normalized.startswith('kind:') or line_normalized.startswith('type:'):
                        current_interface['kind'] = line_stripped.split(':', 1)[1].strip()
                    elif line_normalized.startswith('params:') or line_normalized.startswith('parameters:'):
                        params_str = line_stripped.split(':', 1)[1].strip()
                        # Try parsing { DATA_WIDTH : 64 } format
                        params_match = re.findall(r'(\w+)\s*:\s*(\w+)', params_str)
                        if params_match:
                            current_interface['params'] = dict(params_match)
                        else:
                            # Try parsing [64, 9] format
                            list_match = re.findall(r'\d+', params_str)
                            if list_match:
                                current_interface['params'] = {'values': [int(x) for x in list_match]}
                    elif line_normalized.startswith('map_to_model:'):
                        current_interface['map_to_model'] = line_stripped.split(':', 1)[1].strip()
                    elif line_normalized.startswith('virtual_if:'):
                        current_interface['virtual_if'] = line_stripped.split(':', 1)[1].strip()
        
        # Don't forget the last interface
        if current_interface and current_interface.get('name'):
            data['interfaces'].append(current_interface)
        
        return data
    
    def _validate(self):
        """Validate parsed data has minimum required fields"""
        warnings = []
        
        if not self.data.get('block_name'):
            warnings.append("Block name not found - will use 'unknown_block'")
            self.data['block_name'] = 'unknown_block'
        
        if not self.data.get('clock', {}).get('name'):
            warnings.append("Clock signal not found - will use 'clk'")
            self.data['clock']['name'] = 'clk'
        
        if not self.data.get('reset', {}).get('name'):
            warnings.append("Reset signal not found - will use 'resetn'")
            self.data['reset']['name'] = 'resetn'
        
        if not self.data.get('interfaces'):
            warnings.append("No interfaces found - prompts will have limited context")
        
        for warning in warnings:
            logger.warning(f"Block YAML: {warning}")
    
    # Public API
    def get_block_name(self) -> str:
        return self.data['block_name']
    
    def get_interfaces(self) -> List[Dict]:
        return self.data['interfaces']
    
    def get_clock(self) -> Dict:
        return self.data['clock']
    
    def get_reset(self) -> Dict:
        return self.data['reset']
    
    def get_model(self) -> Dict:
        return self.data.get('model', {})
    
    def get_interface_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific interface by name"""
        for iface in self.data['interfaces']:
            if iface['name'] == name:
                return iface
        return None
    
    def get_interface_names(self) -> List[str]:
        """Get list of all interface names"""
        return [iface['name'] for iface in self.data['interfaces']]
    
    def to_dict(self) -> Dict:
        return self.data


class VplanYAMLParser:
    """
    Parser for Vplan YAML file (test case specifications)
    
    Key Improvements:
    - Generic parameter extraction (not hardcoded)
    - Supports multiple vplan structures
    - Better error handling
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Vplan YAML not found: {file_path}")
        
        self.raw_content = self.file_path.read_text(encoding='utf-8')
        self.data = self._parse()
        self.test_cases = self._extract_test_cases()
    
    def _parse(self) -> Dict[str, Any]:
        """Parse the vplan YAML file"""
        try:
            data = yaml.safe_load(self.raw_content)
            if data is None:
                return {'test_cases': []}
            return data if isinstance(data, dict) else {'test_cases': data}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse vplan YAML: {e}")
            return {'test_cases': []}
    
    def _extract_test_cases(self) -> List[Dict]:
        """Extract test cases from parsed data"""
        # Handle different vplan structures
        if isinstance(self.data, list):
            return self.data
        
        # Try common keys
        for key in ['test_cases', 'tests', 'testcases', 'TestCases']:
            if key in self.data:
                tc_data = self.data[key]
                return tc_data if isinstance(tc_data, list) else [tc_data]
        
        # If data itself looks like a single test case
        if 'TC_ID' in self.data or 'tc_id' in self.data:
            return [self.data]
        
        return []
    
    def get_test_cases(self) -> List[Dict]:
        return self.test_cases
    
    def get_test_case_by_id(self, tc_id: str) -> Optional[Dict]:
        for tc in self.test_cases:
            if tc.get('TC_ID', tc.get('tc_id', '')) == tc_id:
                return tc
        return None
    
    def extract_config(self, tc: Dict) -> Dict:
        """
        Extract configuration parameters from a test case
        
        GENERIC: Extracts all parameters dynamically, not hardcoded
        """
        config = {
            'tc_id': tc.get('TC_ID', tc.get('tc_id', '')),
            'active_uvcs': tc.get('Active_UVCs', tc.get('active_uvcs', [])),
            'parameters': {},  # All extracted parameters
            'patterns': {},
            'coverage': [],
            'raw': tc  # Keep raw data for custom access
        }
        
        # Extract from Stimulus_Generation (handle both list and dict formats)
        stim_gen = tc.get('Stimulus_Generation', tc.get('stimulus_generation', {}))
        
        if isinstance(stim_gen, list):
            for item in stim_gen:
                self._extract_params_from_dict(item, config)
        elif isinstance(stim_gen, dict):
            self._extract_params_from_dict(stim_gen, config)
        
        # Extract coverage intent
        coverage = tc.get('Coverage_Intent', tc.get('coverage_intent', {}))
        if isinstance(coverage, dict):
            config['coverage'] = coverage.get('functional', [])
        
        # Auto-detect and set common parameters with defaults
        self._set_common_defaults(config)
        
        return config
    
    def _extract_params_from_dict(self, data: Dict, config: Dict):
        """Recursively extract parameters from nested dicts"""
        if not isinstance(data, dict):
            return
        
        for key, value in data.items():
            if key in ['regbank_program', 'config', 'configuration', 'params']:
                if isinstance(value, dict):
                    config['parameters'].update(value)
            elif key in ['input_provisioning', 'data_patterns', 'patterns']:
                if isinstance(value, dict):
                    config['patterns'].update(value)
            elif isinstance(value, dict):
                # Recurse into nested dicts
                self._extract_params_from_dict(value, config)
            else:
                # Store at top level of parameters
                config['parameters'][key] = value
    
    def _set_common_defaults(self, config: Dict):
        """Set defaults for common parameters if not present"""
        params = config['parameters']
        
        # Common parameter defaults (these can be overridden per IP via settings)
        defaults = {
            'mode': '00',
            'sign_8b': 'dont_care'
        }
        
        for key, default_val in defaults.items():
            if key not in params:
                # Check alternative keys
                alt_keys = {
                    'mode': ['operation_mode', 'op_mode', 'MODE'],
                    'sign_8b': ['sign', 'signed', 'SIGN']
                }
                found = False
                for alt in alt_keys.get(key, []):
                    if alt in params:
                        params[key] = params[alt]
                        found = True
                        break
                if not found:
                    params[key] = default_val
    
    def get_param_value(self, tc_config: Dict, param_name: str, default: Any = None) -> Any:
        """Get a parameter value with fallback to default"""
        return tc_config.get('parameters', {}).get(param_name, default)


class ParameterTransformer:
    """
    Transform parameter values between string/int representations
    
    Configurable via settings - not hardcoded
    """
    
    def __init__(self, transformations: Dict = None):
        self.transformations = transformations or {}
    
    def transform(self, param_name: str, value: str) -> Any:
        """Transform a parameter value"""
        if param_name in self.transformations:
            mapping = self.transformations[param_name]
            if isinstance(mapping, dict):
                return mapping.get(value, mapping.get('default', value))
        return value
    
    def get_mode_int(self, mode_str: str) -> int:
        """Convert mode string to integer"""
        mode_map = self.transformations.get('mode', {})
        if isinstance(mode_map, dict):
            entry = mode_map.get(mode_str, {})
            if isinstance(entry, dict):
                return entry.get('value', 0)
            return entry if isinstance(entry, int) else 0
        # Fallback default mapping
        default_map = {'00': 0, '01': 1, '10': 2, '11': 3}
        return default_map.get(mode_str, 0)
    
    def get_sign_int(self, sign_str: str) -> int:
        """Convert sign_8b string to integer"""
        if sign_str == 'dont_care':
            return 0
        sign_map = self.transformations.get('sign_8b', {})
        if isinstance(sign_map, dict) and sign_str in sign_map:
            return sign_map[sign_str]
        # Fallback default mapping
        default_map = {'00': 0, '01': 1, '10': 2, '11': 3, 'dont_care': 0}
        return default_map.get(sign_str, 0)
    
    def get_ps_flags(self, ps_phase: str) -> Dict[str, int]:
        """Get PS flags from phase string"""
        ps_map = self.transformations.get('ps_phase', {})
        if ps_phase in ps_map:
            return ps_map[ps_phase]
        # Fallback defaults
        defaults = {
            'PS_FIRST': {'PS_FIRST': 1, 'PS_MODE': 0, 'PS_LAST': 0},
            'PS_MODE': {'PS_FIRST': 0, 'PS_MODE': 1, 'PS_LAST': 0},
            'PS_LAST': {'PS_FIRST': 0, 'PS_MODE': 0, 'PS_LAST': 1}
        }
        return defaults.get(ps_phase, {'PS_FIRST': 1, 'PS_MODE': 0, 'PS_LAST': 0})


def load_uvc_mapping(config_path: str) -> Dict:
    """Load UVC mapping configuration"""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"UVC mapping not found: {config_path} - using empty mapping")
        return {'uvc_mapping': {}, 'transformations': {}, 'packages': []}
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def load_settings(config_path: str) -> Dict:
    """Load settings configuration"""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Settings not found: {config_path} - using defaults")
        return {
            'llm': {'provider': 'anthropic', 'model': 'claude-sonnet-4-20250514', 'max_tokens': 8192},
            'output': {'base_dir': './output'},
            'naming': {}
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}
