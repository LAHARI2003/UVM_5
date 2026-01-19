"""
Prompts for Phase A: IP Infrastructure Generation - V2 (Dynamic/Generic)

Key Improvements:
- All names derived from input, not hardcoded
- Interface types extracted from block YAML
- Signal names generated from interface definitions
- Supports arbitrary IP blocks
"""

from typing import Dict, List, Optional


def format_interfaces_for_prompt(interfaces: List[Dict], uvc_mapping: Dict = None) -> str:
    """Format interface list for inclusion in prompts"""
    if not interfaces:
        return "No interfaces defined in Block YAML"
    
    lines = []
    uvc_map = uvc_mapping.get('uvc_mapping', {}) if uvc_mapping else {}
    
    for iface in interfaces:
        name = iface.get('name', 'unknown')
        kind = iface.get('kind', 'unknown_env')
        params = iface.get('params', {})
        
        # Format parameters
        if isinstance(params, dict):
            if 'values' in params:
                param_str = ', '.join(str(v) for v in params['values'])
            else:
                param_str = ', '.join(f"{k}={v}" for k, v in params.items())
        else:
            param_str = str(params)
        
        # Get additional info from UVC mapping if available
        mapping_info = uvc_map.get(name, {})
        seq_type = mapping_info.get('sequencer_type', '')
        
        if param_str:
            lines.append(f"  - {name}: {kind}#({param_str})")
        else:
            lines.append(f"  - {name}: {kind}")
        
        if seq_type:
            lines.append(f"      Sequencer: {seq_type}")
    
    return '\n'.join(lines)


def format_sequencer_declarations(interfaces: List[Dict], uvc_mapping: Dict = None) -> str:
    """Generate sequencer declarations from interfaces"""
    lines = []
    uvc_map = uvc_mapping.get('uvc_mapping', {}) if uvc_mapping else {}
    
    for iface in interfaces:
        name = iface.get('name', 'unknown')
        kind = iface.get('kind', '')
        params = iface.get('params', {})
        
        # Get sequencer info from mapping or derive from kind
        mapping_info = uvc_map.get(name, {})
        seq_type = mapping_info.get('sequencer_type', '')
        seq_name = mapping_info.get('sequencer_name', f"seqr_{name.replace('m_', '').replace('_env', '')}")
        
        if not seq_type:
            # Derive from kind (e.g., istream_env -> istream_sequencer)
            seq_type = kind.replace('_env', '_sequencer') if kind else 'uvm_sequencer'
        
        # Add parameters if present
        if isinstance(params, dict) and 'values' in params:
            param_str = ', '.join(str(v) for v in params['values'])
            if param_str:
                seq_type = f"{seq_type}#({param_str})"
        
        lines.append(f"  {seq_type} {seq_name};")
    
    return '\n'.join(lines)


def get_env_prompt(
    block_yaml: str,
    interfaces: List[Dict],
    uvc_info: str,
    example_env: str,
    env_class_name: str,
    vseqr_class_name: str,
    uvc_mapping: Dict = None
) -> str:
    """Generate prompt for environment file - DYNAMIC version"""
    
    interface_list = format_interfaces_for_prompt(interfaces, uvc_mapping)
    
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM environment class.

## Block Description (from YAML):
```
{block_yaml}
```

## Interfaces to instantiate:
{interface_list}

## Available UVC Information:
```systemverilog
{uvc_info}
```

## Example Environment (follow this structure and style):
```systemverilog
{example_env}
```

## Requirements:
1. Class name: `{env_class_name}`
2. Extend `uvm_env`
3. Use `uvm_component_utils({env_class_name})` macro

4. **Sub-environment instances**: Create ONE instance for EACH interface listed above
   - Use the exact UVC types from the interface list (e.g., istream_env#(64), dpmem_env#(64,9))
   - Instance names should match interface names from Block YAML

5. **Virtual sequencer**: Create instance named `v_seqr` of type `{vseqr_class_name}`

6. **Scoreboard**: Create a scoreboard instance (derive name from env class)

7. **build_phase()**:
   - Call super.build_phase(phase)
   - Create all sub-environments using type_id::create()
   - Create virtual sequencer using type_id::create()
   - Create scoreboard using type_id::create()
   - Get virtual interfaces from uvm_config_db for each sub-environment

8. **connect_phase()**:
   - Call super.connect_phase(phase)
   - Connect each sub-sequencer to virtual sequencer: `v_seqr.<seqr_name> = <env_instance>.m_agent.m_sequencer;`
   - Connect monitor analysis ports to scoreboard where applicable

9. Follow the coding style from the example
10. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete environment file:
"""


def get_virtual_sequencer_prompt(
    block_yaml: str,
    interfaces: List[Dict],
    example_vseqr: str,
    vseqr_class_name: str,
    dut_if_name: str,
    uvc_mapping: Dict = None
) -> str:
    """Generate prompt for virtual sequencer file - DYNAMIC version"""
    
    sequencer_declarations = format_sequencer_declarations(interfaces, uvc_mapping)
    
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM virtual sequencer class.

## Block Description:
```
{block_yaml}
```

## Sequencer pointers to declare (derived from Block YAML interfaces):
```systemverilog
{sequencer_declarations}
```

## Example Virtual Sequencer (follow this structure):
```systemverilog
{example_vseqr}
```

## Requirements:
1. Class name: `{vseqr_class_name}`
2. Extend `uvm_sequencer`
3. Use `uvm_component_utils({vseqr_class_name})` macro

4. **Sequencer POINTERS** (not instances): Declare pointers to sub-sequencers for EACH interface
   - Use the sequencer declarations shown above
   - These are POINTERS that will be connected in the environment's connect_phase

5. **Virtual interface**: `virtual {dut_if_name} vif;`

6. **new() constructor**: Standard uvm_sequencer constructor

7. **build_phase()**: 
   - Call super.build_phase(phase)
   - Get virtual interface from uvm_config_db

8. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete virtual sequencer file:
"""


def get_interface_prompt(
    block_yaml: str,
    interfaces: List[Dict],
    example_interface: str,
    interface_name: str,
    clock_name: str,
    reset_name: str,
    additional_signals: List[str] = None
) -> str:
    """Generate prompt for interface file - DYNAMIC version"""
    
    # Build signal suggestions from interface info
    signal_suggestions = []
    for iface in interfaces:
        name = iface.get('name', '').replace('m_', '').replace('_env', '')
        kind = iface.get('kind', '')
        
        if 'buffer' in name.lower() or 'stream' in kind.lower():
            signal_suggestions.append(f"  // {name} status signals")
            signal_suggestions.append(f"  logic {name}_full;")
            signal_suggestions.append(f"  logic {name}_empty;")
    
    signal_str = '\n'.join(signal_suggestions) if signal_suggestions else "  // Add DUT-specific signals here"
    
    additional_str = ""
    if additional_signals:
        additional_str = "\n## Additional signals to include:\n" + '\n'.join(f"  - {s}" for s in additional_signals)
    
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog interface for the DUT.

## Block Description:
```
{block_yaml}
```

## Example Interface (follow this structure and style):
```systemverilog
{example_interface}
```

## Suggested signals based on interfaces:
```systemverilog
{signal_str}
```
{additional_str}

## Requirements:
1. Interface name: `{interface_name}`
2. Clock port: `input logic {clock_name}`
3. Reset port: `input logic {reset_name}` (assume active low if name contains 'n')

4. **Control signals**: Include common control signals like:
   - Soft reset, enable signals
   - Configuration inputs
   - Any test/scan signals if applicable

5. **Status signals**: Include status outputs like:
   - Buffer full/empty flags for stream interfaces
   - Done/busy indicators
   - Error flags

6. **Clocking block**: Create a clocking block named `cb` at posedge of clock

7. **Initial block**: Set default values for control signals

8. **Helper tasks** (optional): Add tasks for common operations like:
   - capture_output_data(string file_path) for loading golden data
   - wait_for_completion() for polling done signals

9. Use the coding style from the example
10. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete interface file:
"""


def get_scoreboard_prompt(
    block_yaml: str,
    interfaces: List[Dict],
    example_scoreboard: str,
    scoreboard_class_name: str,
    env_class_name: str
) -> str:
    """Generate prompt for scoreboard file - NEW in V2"""
    
    # Identify input and output interfaces
    input_ifaces = []
    output_ifaces = []
    
    for iface in interfaces:
        kind = iface.get('kind', '').lower()
        name = iface.get('name', '')
        
        if 'ostream' in kind or 'output' in name.lower():
            output_ifaces.append(name)
        elif 'istream' in kind or 'input' in name.lower() or 'mem' in kind:
            input_ifaces.append(name)
    
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM scoreboard class.

## Block Description:
```
{block_yaml}
```

## Input interfaces (for reference data):
{chr(10).join(f'  - {i}' for i in input_ifaces) if input_ifaces else '  - None identified'}

## Output interfaces (for checking):
{chr(10).join(f'  - {i}' for i in output_ifaces) if output_ifaces else '  - None identified'}

## Example Scoreboard (if available, follow this style):
```systemverilog
{example_scoreboard if example_scoreboard else '// No example provided - use standard UVM scoreboard pattern'}
```

## Requirements:
1. Class name: `{scoreboard_class_name}`
2. Extend `uvm_scoreboard`
3. Use `uvm_component_utils({scoreboard_class_name})` macro

4. **Analysis imports**: Declare uvm_analysis_imp for receiving transactions

5. **Expected data storage**: 
   - Queue or associative array for expected/golden data
   - Method to load expected data from file

6. **Comparison logic**:
   - write() function to receive actual data
   - Compare actual vs expected
   - Report mismatches with `uvm_error

7. **Statistics**: Track matches, mismatches, total comparisons

8. **report_phase()**: Print summary of comparison results

9. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete scoreboard file:
"""


def get_package_prompt(
    block_yaml: str,
    example_package: str,
    package_name: str,
    vseq_includes: List[str],
    test_includes: List[str],
    env_file: str,
    vseqr_file: str,
    scoreboard_file: str,
    interface_file: str,
    uvc_packages: List[str] = None
) -> str:
    """Generate prompt for package file - DYNAMIC version"""
    
    vseq_list = '\n'.join([f'  `include "{f}"' for f in vseq_includes]) if vseq_includes else '  // No vseq files yet'
    test_list = '\n'.join([f'  `include "{f}"' for f in test_includes]) if test_includes else '  // No test files yet'
    
    # Default UVC packages if not provided
    if not uvc_packages:
        uvc_packages = ['istream_pkg', 'ostream_pkg', 'dpmem_pkg', 'spmem_pkg']
    
    uvc_imports = '\n'.join([f'  import {pkg}::*;' for pkg in uvc_packages])
    
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM package file.

## Block Description:
```
{block_yaml}
```

## Example Package (follow this structure):
```systemverilog
{example_package}
```

## Files to include:
Infrastructure files (in order):
1. {vseqr_file}
2. {scoreboard_file}
3. {env_file}

Virtual sequence files:
{vseq_list}

Test files:
{test_list}

## UVC package imports:
```systemverilog
{uvc_imports}
```

## Requirements:
1. Package name: `{package_name}`
2. `import uvm_pkg::*;`
3. `include "uvm_macros.svh"`
4. Import all required UVC packages (shown above)
5. Include infrastructure files in correct order (virtual_sequencer before env)
6. Include all virtual sequence files
7. Include all test files
8. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete package file:
"""
