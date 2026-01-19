"""
Prompts for Phase A: IP Infrastructure Generation
"""

def get_env_prompt(block_yaml: str, uvc_info: str, example_env: str, 
                   env_class_name: str, vseqr_class_name: str) -> str:
    """Generate prompt for environment file"""
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM environment class.

## Block Description:
```
{block_yaml}
```

## Available UVC Information:
```systemverilog
{uvc_info}
```

## Example Environment (follow this structure EXACTLY):
```systemverilog
{example_env}
```

## Requirements:
1. Class name: {env_class_name}
2. Extend uvm_env
3. Instantiate ALL sub-environments listed in Block Description:
   - Use the exact UVC types from the Block Description (e.g., istream_env#(64), dpmem_env#(64,9))
   - Each interface from Block Description needs a sub-environment instance
4. Create virtual sequencer: {vseqr_class_name}
5. Create scoreboard instance
6. In build_phase():
   - Create all sub-environments using type_id::create
   - Create virtual sequencer
   - Create scoreboard
   - Get ALL virtual interfaces from config_db (one for each sub-environment)
7. In connect_phase():
   - Connect each sub-sequencer to virtual sequencer (v_seqr.seqr_xxx = m_xxx_env.m_agent.m_sequencer)
   - Connect agent virtual interfaces
   - Connect monitor ports to scoreboard where applicable
8. Use `uvm_component_utils macro
9. Follow the EXACT naming conventions from the example
10. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete environment file:
"""


def get_virtual_sequencer_prompt(block_yaml: str, example_vseqr: str,
                                  vseqr_class_name: str, dut_if_name: str) -> str:
    """Generate prompt for virtual sequencer file"""
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM virtual sequencer class.

## Block Description:
```
{block_yaml}
```

## Example Virtual Sequencer (follow this structure EXACTLY):
```systemverilog
{example_vseqr}
```

## Requirements:
1. Class name: {vseqr_class_name}
2. Extend uvm_sequencer
3. Declare sequencer POINTERS (not instances) for each sub-environment:
   - istream_sequencer#(64) for feature buffer
   - dpmem_sequencer#(64,9) for kernel memory
   - ostream_sequencer#(64) for output buffer
   - istream_sequencer#(32) for psin
   - spmem_sequencer#(64,4) for addin
   - computation_sequencer for computation
4. Declare virtual interface: virtual {dut_if_name} vif
5. Use `uvm_component_utils macro
6. In build_phase():
   - Get virtual interface from config_db
7. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete virtual sequencer file:
"""


def get_interface_prompt(block_yaml: str, example_interface: str,
                         interface_name: str, clock_name: str, reset_name: str) -> str:
    """Generate prompt for interface file"""
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog interface for the DUT.

## Block Description:
```
{block_yaml}
```

## Example Interface (follow this structure EXACTLY):
```systemverilog
{example_interface}
```

## Requirements:
1. Interface name: {interface_name}
2. Clock port: {clock_name}
3. Reset port: {reset_name} (active low based on Block Description)
4. Include control signals (inputs to DUT):
   - SOFT_RESET, DISABLE_STALL, DISABLE_PS_STALL, DISABLE_SOUT_STALL, DISABLE_PSOUT_STALL
   - CG_DISABLE, feat_en, tile_en, valid_feat_count, psout_mode, compute_mask
   - Test signals: test_si, tst_scanmode, tst_scanenable, test_clk
5. Include status signals (outputs from DUT):
   - test_so
   - Buffer full/empty flags: feat_buff_full, feat_buff_empty, psin_buff_full, psin_buff_empty
   - sout_buff_full, sout_buff_empty, psout_buff_full, psout_buff_empty
6. Include helper signals:
   - capture_output_buffer_exp_data, output_buffer_exp_data_size
7. Create clocking block 'cb' at posedge of clock
8. Add initial block with default values
9. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete interface file:
"""


def get_package_prompt(block_yaml: str, example_package: str, package_name: str,
                       vseq_includes: list, test_includes: list,
                       env_file: str, vseqr_file: str, scoreboard_file: str) -> str:
    """Generate prompt for package file"""
    vseq_list = '\n'.join([f'  `include "{f}"' for f in vseq_includes])
    test_list = '\n'.join([f'  `include "{f}"' for f in test_includes])
    
    return f"""You are a UVM verification expert. Generate a complete SystemVerilog UVM package file.

## Block Description:
```
{block_yaml}
```

## Example Package (follow this structure EXACTLY):
```systemverilog
{example_package}
```

## Files to include:
Infrastructure files:
- {vseqr_file}
- {scoreboard_file}
- {env_file}

Virtual sequence files:
{vseq_list}

Test files:
{test_list}

## Requirements:
1. Package name: {package_name}
2. Import uvm_pkg::*
3. Import all UVC packages:
   - istream_pkg
   - dpmem_pkg
   - spmem_pkg
   - computation_pkg
   - ostream_pkg
4. Include uvm_macros.svh
5. Include infrastructure files (virtual_sequencer, scoreboard, env)
6. Include ALL virtual sequence files listed above
7. Include ALL test files listed above
8. Output ONLY valid SystemVerilog code - no explanations, no markdown

Generate the complete package file:
"""
