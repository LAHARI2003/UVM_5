"""
Prompts for Phase B: Test Case Generation
"""

import yaml


def get_test_prompt(tc_config: dict, example_test: str, env_class: str, 
                    vseqr_class: str, dut_if_name: str) -> str:
    """Generate prompt for test file"""
    tc_id = tc_config['tc_id']
    mode = tc_config.get('mode', 0)
    sign_8b = tc_config.get('sign_8b', 0)
    
    return f"""You are a UVM verification expert. Generate a complete UVM test class.

## Test Case Configuration:
- TC_ID: {tc_id}
- Mode: {tc_config.get('mode', '00')} (integer: {mode})
- Sign_8b: {tc_config.get('sign_8b', '0')} (integer: {sign_8b})
- PS_Phase: {tc_config.get('ps_phase', 'PS_FIRST')}

## Example Test (follow this structure EXACTLY):
```systemverilog
{example_test}
```

## Requirements:
1. Class name: {tc_id}_test
2. Extend uvm_test
3. Use `uvm_component_utils({tc_id}_test)
4. Declare:
   - {env_class} env;
   - {tc_id}_vseq vseq_compu;
   - virtual {dut_if_name} vif;
5. In new(): call super.new(name, parent)
6. In build_phase():
   - Create env using type_id::create("env", this)
   - Create vseq using type_id::create with $sformatf for name including mode and sign
   - Get virtual interface from config_db using key "{dut_if_name.replace('_if', '')}_vif"
7. In run_phase():
   - raise_objection
   - wait for resetn == 1
   - repeat(5) @(vif.cb)
   - Start vseq: vseq_compu.start(env.v_seqr)
   - repeat(10) @(vif.cb)
   - drop_objection
8. In connect_phase(): call super.connect_phase(phase)
9. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete test file:
"""


def get_vseq_prompt(tc_config: dict, example_vseq: str, vseqr_class: str,
                    active_uvcs: list, uvc_mapping: dict,
                    generated_vseqr: str = "", c_model_usage: str = "") -> str:
    """Generate prompt for virtual sequence file"""
    tc_id = tc_config['tc_id']
    mode_str = tc_config.get('mode', '00')
    sign_str = tc_config.get('sign_8b', 'dont_care')
    ps_phase = tc_config.get('ps_phase', 'PS_FIRST')
    
    # Convert to integers
    mode_map = {'00': 0, '01': 1, '10': 2, '11': 3}
    mode_int = mode_map.get(mode_str, 0)
    
    sign_map = {'dont_care': 0, '00': 0, '01': 1, '10': 2, '11': 3}
    sign_int = sign_map.get(sign_str, 0)
    
    # PS flags
    ps_first = 1 if ps_phase == 'PS_FIRST' else 0
    ps_mode = 1 if ps_phase == 'PS_MODE' else 0
    ps_last = 1 if ps_phase == 'PS_LAST' else 0
    
    # Determine which sequences to use based on active UVCs
    has_feature = 'm_feature_buffer_env' in active_uvcs
    has_kernel = 'm_kernel_mem_env' in active_uvcs
    has_psin = 'm_psin_env' in active_uvcs
    has_addin = 'm_addin_env' in active_uvcs
    has_output = 'm_output_buffer_env' in active_uvcs
    has_computation = 'm_computation_env' in active_uvcs
    
    active_uvcs_str = '\n'.join([f'  - {uvc}' for uvc in active_uvcs])
    
    # Include generated virtual sequencer info if available
    vseqr_info = ""
    if generated_vseqr:
        vseqr_info = f"""
## Generated Virtual Sequencer (USE THESE EXACT sequencer names from p_sequencer):
```systemverilog
{generated_vseqr}
```
IMPORTANT: The virtual sequencer has these sequencers - use them via p_sequencer:
- p_sequencer.seqr_feature_buffer  (for feature buffer sequences)
- p_sequencer.seqr_kernel_mem      (for kernel memory sequences)
- p_sequencer.seqr_output_buffer   (for output buffer sequences)
- p_sequencer.seqr_psin            (for psin sequences)
- p_sequencer.seqr_addin           (for addin sequences)
- p_sequencer.seqr_compu           (for computation sequences)
- p_sequencer.vif                  (for virtual interface access)
"""
    
    # Include C model usage if available
    c_model_info = ""
    if c_model_usage:
        c_model_info = f"""
## C Reference Model Command Format:
{c_model_usage}
"""
    else:
        c_model_info = """
## C Reference Model Command Format:
./psout_exe kernel_file feature_file psin_hex32_file addin_hex32_file output_file mode sign_8b PS_FIRST PS_MODE PS_LAST

Arguments (in order):
1. kernel_file      - e.g., "./kernel_hex_rtl.txt"
2. feature_file     - e.g., "./feature_hex_rtl.txt"
3. psin_hex32_file  - e.g., "./psin_hex32_input.txt"
4. addin_hex32_file - e.g., "./addin_hex32_input.txt"
5. output_file      - e.g., "./golden.txt"
6. mode             - integer (0-3)
7. sign_8b          - integer (0-3)
8. PS_FIRST         - 0 or 1
9. PS_MODE          - 0 or 1
10. PS_LAST         - 0 or 1

Example: $system($sformatf("./psout_exe ./kernel_hex_rtl.txt ./feature_hex_rtl.txt ./psin_hex32_input.txt ./addin_hex32_input.txt ./golden.txt %0d %0d %0d %0d %0d", mode, sign_8b, PS_FIRST, PS_MODE, PS_LAST));
"""

    return f"""You are a UVM verification expert. Generate a complete UVM virtual sequence.

## Test Case Configuration:
- TC_ID: {tc_id}
- Mode: "{mode_str}" → integer value: {mode_int}
- Sign_8b: "{sign_str}" → integer value: {sign_int}
- PS_Phase: {ps_phase}
  - PS_FIRST = {ps_first}
  - PS_MODE = {ps_mode}
  - PS_LAST = {ps_last}

## Active UVCs for this test (ONLY use these):
{active_uvcs_str}

## Flags:
- has_feature_buffer: {has_feature}
- has_kernel_mem: {has_kernel}
- has_psin: {has_psin}
- has_addin: {has_addin}
- has_output_buffer: {has_output}
- has_computation: {has_computation}
{vseqr_info}
{c_model_info}

## Example Virtual Sequence (follow this structure EXACTLY - especially field assignments and sequencer names):
```systemverilog
{example_vseq}
```

## CRITICAL Requirements - Follow these EXACTLY:
1. Class name: {tc_id}_vseq
2. Extend uvm_sequence
3. Use `uvm_object_utils({tc_id}_vseq)
4. Use `uvm_declare_p_sequencer({vseqr_class})

5. Declare sequences ONLY for active UVCs:
   - If has_feature: istream_directed_write_sequence#(64) seq_feat_wr;
   - If has_kernel: dpmem_directed_write_sequence#(64,9) seq_ker_wr;
   - If has_psin: istream_directed_write_sequence#(32) seq_psin_wr;
   - If has_addin: spmem_directed_write_sequence#(64,4) seq_addin_wr;
   - Always: computation_configure_write_seq seq_compu_wr;
   - If has_output: ostream_random_burst_read_sequence#(64) seq_outbuf_rd;

6. Declare variables: int mode, feature_buffer_size, sign_8b, PS_FIRST, PS_MODE, PS_LAST

7. In new(): call super.new(name) with default name "{tc_id}_vseq"

8. **CRITICAL - Sequencer Access**: Use these EXACT paths when starting sequences:
   - seq_feat_wr.start(p_sequencer.seqr_feature_buffer);
   - seq_ker_wr.start(p_sequencer.seqr_kernel_mem);
   - seq_psin_wr.start(p_sequencer.seqr_psin);
   - seq_addin_wr.start(p_sequencer.seqr_addin);
   - seq_compu_wr.start(p_sequencer.seqr_compu);
   - seq_outbuf_rd.start(p_sequencer.seqr_output_buffer);
   - Virtual interface: p_sequencer.vif

9. **CRITICAL - Sequence Field Assignment**: Use DIRECT assignment, NOT randomize with constraints:
   CORRECT:
     seq_feat_wr.size = 16;
     seq_feat_wr.file_path = "./feature_hex_rtl.txt";
   
   WRONG (do NOT use):
     seq_feat_wr.randomize() with {{ size == 16; filename == "..."; }}

10. **CRITICAL - Field Names**: Use exact field names:
    - Use 'file_path' (not 'filename')
    - Use 'size' for data size

11. In body() task:
    a. Set parameters:
       - mode = {mode_int};
       - feature_buffer_size = 1;
       - sign_8b = {sign_int};
       - PS_FIRST = {ps_first};
       - PS_MODE = {ps_mode};
       - PS_LAST = {ps_last};
    
    b. Generate stimulus data using $system calls:
       - Call: python generate_data_hex_unique.py with mode, feature_buffer_size, sign_8b
       - If has_psin: Call python generate_data_psin_addin.py
       - Call C model with EXACT format: ./psout_exe kernel feat psin addin output mode sign PS_FIRST PS_MODE PS_LAST
    
    c. Setup capture on p_sequencer.vif.capture_output_buffer_exp_data(file_path)
    
    d. Initialize computation (START_COMPUTE=0, COMPE=0)
    
    e. Write input data sequences (ONLY for active UVCs):
       - Feature buffer: size=16, file_path="./feature_hex_rtl.txt", start on seqr_feature_buffer
       - Kernel memory: size=512, file_path="./kernel_hex_rtl.txt", start on seqr_kernel_mem
       - PSIN (if active): size=32, file_path="./psin_hex_rtl.txt", start on seqr_psin
       - ADDIN (if active): size=16, file_path="./addin_hex_rtl.txt", start on seqr_addin
    
    f. Start computation (START_COMPUTE=1, COMPE=1)
    
    g. Wait for psout_buff_full == 1
    
    h. Read output buffer: size=32, start on seqr_output_buffer
    
    i. Cleanup: $system calls to remove/rename temp files

12. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete virtual sequence file:
"""
