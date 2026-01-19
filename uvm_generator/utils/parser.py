"""
YAML Parsers for Block and Vplan files
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class BlockYAMLParser:
    """Parser for Block YAML file (IP description)"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.raw_content = self.file_path.read_text()
        self.data = self._parse()
    
    def _parse(self) -> Dict[str, Any]:
        """Parse the block YAML file (handles non-standard format)"""
        data = {
            'block_name': '',
            'clock': {'name': '', 'frequency': ''},
            'reset': {'name': '', 'active_low': False},
            'model': {'language': '', 'entry': '', 'lib_path': ''},
            'interfaces': []
        }
        
        lines = self.raw_content.split('\n')
        current_section = None
        current_interface = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse block name
            if line.startswith('Name :') and current_section != 'interfaces':
                if 'Block' in self.raw_content[:self.raw_content.find(line)]:
                    data['block_name'] = line.split(':')[1].strip()
            
            # Parse clock
            if line.startswith('name :') and 'Clocks' in self.raw_content[:self.raw_content.find(line)]:
                data['clock']['name'] = line.split(':')[1].strip()
            if line.startswith('Frequency :'):
                data['clock']['frequency'] = line.split(':')[1].strip()
            
            # Parse reset
            if line.startswith('Name :') and 'Resets' in self.raw_content[:self.raw_content.find(line)]:
                data['reset']['name'] = line.split(':')[1].strip()
            if line.startswith('Active_low :'):
                data['reset']['active_low'] = 'true' in line.lower()
            
            # Parse model
            if line.startswith('Language :'):
                data['model']['language'] = line.split(':')[1].strip()
            if line.startswith('Entry :'):
                data['model']['entry'] = line.split(':')[1].strip()
            if line.startswith('lib_path :'):
                data['model']['lib_path'] = line.split(':')[1].strip()
            
            # Parse interfaces section
            if 'Interfaces' in line:
                current_section = 'interfaces'
                continue
            
            if current_section == 'interfaces':
                if line.startswith('Name :'):
                    if current_interface:
                        data['interfaces'].append(current_interface)
                    current_interface = {
                        'name': line.split(':')[1].strip(),
                        'kind': '',
                        'params': {},
                        'map_to_model': ''
                    }
                elif line.startswith('Kind :') and current_interface:
                    current_interface['kind'] = line.split(':')[1].strip()
                elif line.startswith('params :') and current_interface:
                    params_str = line.split(':')[1].strip()
                    # Parse { DATA_WIDTH : 64 } format
                    params_match = re.findall(r'(\w+)\s*:\s*(\w+)', params_str)
                    current_interface['params'] = dict(params_match)
                elif line.startswith('Map_to_model :') and current_interface:
                    current_interface['map_to_model'] = line.split(':')[1].strip()
        
        # Don't forget the last interface
        if current_interface:
            data['interfaces'].append(current_interface)
        
        return data
    
    def get_block_name(self) -> str:
        return self.data['block_name']
    
    def get_interfaces(self) -> List[Dict]:
        return self.data['interfaces']
    
    def get_clock(self) -> Dict:
        return self.data['clock']
    
    def get_reset(self) -> Dict:
        return self.data['reset']
    
    def to_dict(self) -> Dict:
        return self.data


class VplanYAMLParser:
    """Parser for Vplan YAML file (test case specifications)"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.raw_content = self.file_path.read_text()
        self.test_cases = self._parse()
    
    def _parse(self) -> List[Dict[str, Any]]:
        """Parse the vplan YAML file"""
        # The file is a list of test cases
        data = yaml.safe_load(self.raw_content)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            return []
    
    def get_test_cases(self) -> List[Dict]:
        return self.test_cases
    
    def get_test_case_by_id(self, tc_id: str) -> Optional[Dict]:
        for tc in self.test_cases:
            if tc.get('TC_ID') == tc_id:
                return tc
        return None
    
    def extract_config(self, tc: Dict) -> Dict:
        """Extract configuration parameters from a test case"""
        config = {
            'tc_id': tc.get('TC_ID', ''),
            'active_uvcs': tc.get('Active_UVCs', []),
            'mode': '00',
            'sign_8b': '0',
            'ps_phase': 'PS_FIRST',
            'ps_first': 0,
            'ps_mode': 0,
            'ps_last': 0,
            'patterns': {}
        }
        
        # Extract from Stimulus_Generation
        stim_gen = tc.get('Stimulus_Generation', [])
        for item in stim_gen:
            if 'regbank_program' in item:
                reg = item['regbank_program']
                config['mode'] = reg.get('mode', '00')
                config['sign_8b'] = reg.get('sign_8b', 'dont_care')
                config['ps_phase'] = reg.get('ps_phase', 'PS_FIRST')
                
                # Set PS flags
                if config['ps_phase'] == 'PS_FIRST':
                    config['ps_first'], config['ps_mode'], config['ps_last'] = 1, 0, 0
                elif config['ps_phase'] == 'PS_MODE':
                    config['ps_first'], config['ps_mode'], config['ps_last'] = 0, 1, 0
                elif config['ps_phase'] == 'PS_LAST':
                    config['ps_first'], config['ps_mode'], config['ps_last'] = 0, 0, 1
            
            if 'input_provisioning' in item:
                prov = item['input_provisioning']
                for target, details in prov.items():
                    if isinstance(details, dict):
                        config['patterns'][target] = details.get('pattern_bin', '')
        
        return config
    
    def get_mode_int(self, mode_str: str) -> int:
        """Convert mode string to integer"""
        mapping = {'00': 0, '01': 1, '10': 2, '11': 3}
        return mapping.get(mode_str, 0)
    
    def get_sign_int(self, sign_str: str) -> int:
        """Convert sign_8b string to integer"""
        if sign_str == 'dont_care':
            return 0
        mapping = {'00': 0, '01': 1, '10': 2, '11': 3}
        return mapping.get(sign_str, 0)


def load_uvc_mapping(config_path: str) -> Dict:
    """Load UVC mapping configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_settings(config_path: str) -> Dict:
    """Load settings configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
