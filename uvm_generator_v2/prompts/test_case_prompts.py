"""
Prompts for Phase B: Test Case Generation - V2 (Dynamic/Generic)

Key Improvements:
- No hardcoded interface names (m_feature_buffer_env, etc.)
- Dynamic UVC flag detection from active_uvcs list
- C model command format from block YAML or config
- Sequencer names derived from generated virtual sequencer
"""

from typing import Dict, List, Optional, Any


def extract_active_uvc_info(active_uvcs: List[str], uvc_mapping: Dict) -> Dict[str, Dict]:
    """
    Extract information about active UVCs from mapping
    
    Returns dict mapping UVC name to its sequence/sequencer info
    """
    uvc_map = uvc_mapping.get('uvc_mapping', {}) if uvc_mapping else {}
    
    active_info = {}
    for uvc_name in active_uvcs:
        if uvc_name in uvc_map:
            active_info[uvc_name] = uvc_map[uvc_name]
        else:
            # Derive basic info from name
            short_name = uvc_name.replace('m_', '').replace('_env', '')
            active_info[uvc_name] = {
                'sequencer_name': f'seqr_{short_name}',
                'sequences': {}
            }
    
    return active_info


def format_active_uvcs_for_prompt(active_uvcs: List[str], uvc_mapping: Dict) -> str:
    """Format active UVCs with their sequencer info for prompts"""
    uvc_map = uvc_mapping.get('uvc_mapping', {}) if uvc_mapping else {}
    
    lines = []
    for uvc_name in active_uvcs:
        mapping = uvc_map.get(uvc_name, {})
        seq_name = mapping.get('sequencer_name', f"seqr_{uvc_name.replace('m_', '').replace('_env', '')}")
        seq_type = mapping.get('sequencer_type', 'uvm_sequencer')
        
        sequences = mapping.get('sequences', {})
        write_seq = sequences.get('write', sequences.get('configure', ''))
        read_seq = sequences.get('read', '')
        
        lines.append(f"  - {uvc_name}")
        lines.append(f"      Sequencer: p_sequencer.{seq_name}")
        if write_seq:
            lines.append(f"      Write sequence: {write_seq}")
        if read_seq:
            lines.append(f"      Read sequence: {read_seq}")
    
    return '\n'.join(lines)


def format_c_model_info(model_config: Dict) -> str:
    """Format C model information for prompts"""
    if not model_config:
        return """
## C Reference Model:
No C model configuration provided. Generate placeholder $system calls with comments.
Example: $system("./reference_model input.txt output.txt");
"""
    
    executable = model_config.get('executable', './model_exe')
    command_format = model_config.get('command_format', '')
    arguments = model_config.get('arguments', [])
    
    if command_format:
        return f"""
## C Reference Model Command Format:
```
{command_format}
```
Executable: {executable}
"""
    
    if arguments:
        args_str = ' '.join(f'<{arg}>' for arg in arguments)
        return f"""
## C Reference Model:
Executable: {executable}
Arguments: {args_str}
Example: $system($sformatf("{executable} %s %s ...", arg1, arg2));
"""
    
    return f"""
## C Reference Model:
Executable: {executable}
(No specific command format provided - use appropriate arguments based on test config)
"""


def get_test_prompt(
    tc_config: Dict,
    example_test: str,
    env_class: str,
    vseqr_class: str,
    dut_if_name: str,
    reset_signal: str = "resetn"
) -> str:
    """Generate prompt for test file - DYNAMIC version"""
    
    tc_id = tc_config.get('tc_id', 'unknown_test')
    parameters = tc_config.get('parameters', {})
    
    # Format parameters for display
    param_lines = '\n'.join([f"  - {k}: {v}" for k, v in parameters.items()])
    
    return f"""You are a UVM verification expert. Generate a complete UVM test class.

## Test Case Configuration:
- TC_ID: {tc_id}
- Parameters:
{param_lines if param_lines else '  (none specified)'}

## Example Test (follow this structure EXACTLY):
```systemverilog
{example_test}
```

## Requirements:
1. Class name: `{tc_id}_test`
2. Extend `uvm_test`
3. Use `uvm_component_utils({tc_id}_test)` macro

4. **Declarations**:
   - `{env_class} env;`
   - `{tc_id}_vseq vseq_compu;`
   - `virtual {dut_if_name} vif;`

5. **new() constructor**: Call `super.new(name, parent)`

6. **build_phase()**:
   - Call super.build_phase(phase)
   - Create env: `env = {env_class}::type_id::create("env", this);`
   - Create vseq: `vseq_compu = {tc_id}_vseq::type_id::create("vseq_compu");`
   - Get virtual interface from uvm_config_db

7. **run_phase()**:
   - raise_objection(this)
   - Wait for reset: `wait(vif.{reset_signal} == 1);`
   - Small delay: `repeat(5) @(vif.cb);`
   - Start vseq: `vseq_compu.start(env.v_seqr);`
   - Post-test delay: `repeat(10) @(vif.cb);`
   - drop_objection(this)

8. **connect_phase()**: Call super.connect_phase(phase)

9. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete test file:
"""


def get_vseq_prompt(
    tc_config: Dict,
    active_uvcs: List[str],
    example_vseq: str,
    vseqr_class: str,
    uvc_mapping: Dict,
    generated_vseqr: str = "",
    model_config: Dict = None
) -> str:
    """Generate prompt for virtual sequence file - DYNAMIC version"""
    
    tc_id = tc_config.get('tc_id', 'unknown_vseq')
    parameters = tc_config.get('parameters', {})
    
    # Format active UVCs with their info
    active_uvcs_str = format_active_uvcs_for_prompt(active_uvcs, uvc_mapping)
    
    # Format C model info
    c_model_info = format_c_model_info(model_config)
    
    # Format parameters
    param_assignments = []
    for key, value in parameters.items():
        if isinstance(value, str) and value.startswith(("'", '"')):
            param_assignments.append(f"    {key} = {value};")
        elif isinstance(value, str):
            # Try to interpret as number or keep as string
            try:
                int(value)
                param_assignments.append(f"    {key} = {value};")
            except ValueError:
                param_assignments.append(f'    {key} = "{value}";')
        else:
            param_assignments.append(f"    {key} = {value};")
    
    param_str = '\n'.join(param_assignments) if param_assignments else '    // No parameters specified'
    
    # Virtual sequencer info
    vseqr_info = ""
    if generated_vseqr:
        vseqr_info = f"""
## Generated Virtual Sequencer (USE THESE EXACT sequencer names):
```systemverilog
{generated_vseqr}
```

IMPORTANT: Access sequencers via p_sequencer.<sequencer_name>
"""
    
    # Build sequence declarations section
    uvc_map = uvc_mapping.get('uvc_mapping', {}) if uvc_mapping else {}
    seq_declarations = []
    seq_start_examples = []
    
    for uvc_name in active_uvcs:
        mapping = uvc_map.get(uvc_name, {})
        seq_name = mapping.get('sequencer_name', f"seqr_{uvc_name.replace('m_', '').replace('_env', '')}")
        sequences = mapping.get('sequences', {})
        
        short_name = uvc_name.replace('m_', '').replace('_env', '')
        
        # Write sequence
        write_seq = sequences.get('write', sequences.get('configure', ''))
        if write_seq:
            var_name = f"seq_{short_name}_wr"
            seq_declarations.append(f"  {write_seq} {var_name};")
            seq_start_examples.append(f"  {var_name}.start(p_sequencer.{seq_name});")
        
        # Read sequence
        read_seq = sequences.get('read', '')
        if read_seq:
            var_name = f"seq_{short_name}_rd"
            seq_declarations.append(f"  {read_seq} {var_name};")
            seq_start_examples.append(f"  {var_name}.start(p_sequencer.{seq_name});")
    
    seq_decl_str = '\n'.join(seq_declarations) if seq_declarations else '  // Declare sequences for active UVCs'
    seq_start_str = '\n'.join(seq_start_examples) if seq_start_examples else '  // Start sequences on appropriate sequencers'

    return f"""You are a UVM verification expert. Generate a complete UVM virtual sequence.

## Test Case Configuration:
- TC_ID: {tc_id}
- Parameters from vplan:
{param_str}

## Active UVCs for this test (ONLY create sequences for these):
{active_uvcs_str}
{vseqr_info}
{c_model_info}

## Sequence declarations to use:
```systemverilog
{seq_decl_str}
```

## How to start sequences (use these patterns):
```systemverilog
{seq_start_str}
```

## Example Virtual Sequence (follow this structure and CODING STYLE):
```systemverilog
{example_vseq}
```

## CRITICAL Requirements - Follow these EXACTLY:

1. Class name: `{tc_id}_vseq`
2. Extend `uvm_sequence`
3. Use `uvm_object_utils({tc_id}_vseq)` macro
4. Use `uvm_declare_p_sequencer({vseqr_class})` macro

5. **Declare sequences ONLY for active UVCs** - use declarations shown above

6. **Declare variables** for test parameters (mode, size, flags, etc.)

7. **new() constructor**: Call super.new(name) with default name "{tc_id}_vseq"

8. **CRITICAL - Sequencer Access**: 
   - Use `p_sequencer.<sequencer_name>` to access sequencers
   - Use `p_sequencer.vif` for virtual interface access

9. **CRITICAL - Sequence Field Assignment**: Use DIRECT assignment, NOT randomize:
   ```systemverilog
   // CORRECT:
   seq_xxx.size = 16;
   seq_xxx.file_path = "./data.txt";
   
   // WRONG (do NOT use):
   seq_xxx.randomize() with {{ size == 16; }};
   ```

10. **CRITICAL - Field Names**: Use these exact names:
    - `file_path` (not 'filename')
    - `size` for data size

11. **body() task structure**:
    a. Set parameters from test config
    b. Generate stimulus data ($system calls for data generation scripts)
    c. Call reference model ($system call with proper format)
    d. Setup golden data capture (if applicable)
    e. Initialize (write configuration)
    f. Write input data (start write sequences)
    g. Trigger operation (start/enable)
    h. Wait for completion (poll status signals)
    i. Read output data (start read sequences)
    j. Cleanup temporary files (optional)

12. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete virtual sequence file:
"""
