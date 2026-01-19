# UVM Test Case Generator - Generic Pipeline Flow

## Overview

This document describes the **model-agnostic** pipeline for generating UVM test cases for **any IP block**. The pipeline takes three inputs and produces a complete, compilable UVM testbench.

---

## Pipeline Inputs

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REQUIRED INPUTS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. VPLAN FILE (YAML)          - Verification plan with test cases          │
│     └─► Test case definitions, active UVCs, stimulus config                 │
│                                                                             │
│  2. BLOCK YAML FILE            - IP block description                       │
│     └─► DUT name, interfaces, clock/reset, UVC types                        │
│                                                                             │
│  3. MODEL.CPP (C/C++ Reference) - Golden reference model                    │
│     └─► Algorithm implementation, command-line interface                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                        ┌──────────────────────┐                             │
│                        │    INPUT FILES       │                             │
│                        └──────────┬───────────┘                             │
│                                   │                                         │
│                                   ▼                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                    PHASE 0: PREPROCESSING                             ║  │
│  ║                    (One-time setup per IP)                            ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║  [0.1] Parse Block YAML → Extract UVC types, interfaces               ║  │
│  ║  [0.2] Parse Model.cpp  → Extract command-line format, I/O files      ║  │
│  ║  [0.3] Generate Config  → uvc_mapping.yaml, settings.yaml             ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                   │                                         │
│                                   ▼                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                    PHASE A: IP INFRASTRUCTURE                         ║  │
│  ║                    (One-time per IP)                                  ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║  [A.1] Generate Environment       → <ip>_env.sv                       ║  │
│  ║  [A.2] Generate Virtual Sequencer → <ip>_virtual_sequencer.sv         ║  │
│  ║  [A.3] Generate Interface         → <ip>_if.sv                        ║  │
│  ║  [A.4] Generate Scoreboard        → <ip>_scoreboard.sv                ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                   │                                         │
│                                   ▼                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                    PHASE B: TEST CASE GENERATION                      ║  │
│  ║                    (Per test case in Vplan)                           ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║  For each test case in Vplan:                                         ║  │
│  ║    [B.1] Generate Test File       → TC_<id>_test.sv                   ║  │
│  ║    [B.2] Generate Virtual Seq     → TC_<id>_vseq.sv                   ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                   │                                         │
│                                   ▼                                         │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                    PHASE C: PACKAGE & INTEGRATION                     ║  │
│  ║                    (Final assembly)                                   ║  │
│  ╠═══════════════════════════════════════════════════════════════════════╣  │
│  ║  [C.1] Generate Package File      → <ip>_pkg.sv                       ║  │
│  ║  [C.2] Generate Filelist          → files.f                           ║  │
│  ╚═══════════════════════════════════════════════════════════════════════╝  │
│                                   │                                         │
│                                   ▼                                         │
│                        ┌──────────────────────┐                             │
│                        │   OUTPUT FILES       │                             │
│                        └──────────────────────┘                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Preprocessing (One-Time Setup)

This phase parses the input files and generates configuration files that the LLM uses in later phases.

### 0.1 Parse Block YAML

**Input:** `block_description.yaml`

**Process:**
```
Block YAML
    │
    ├──► Extract DUT module name
    ├──► Extract clock/reset signals
    ├──► Extract interface list
    │       │
    │       └──► For each interface:
    │               ├── Interface name (e.g., m_feature_buffer_env)
    │               ├── UVC type (e.g., istream_env)
    │               ├── Parameters (e.g., [64] for data width)
    │               └── Virtual interface type
    │
    └──► Output: Parsed block info dictionary
```

**Example Block YAML (Generic):**
```yaml
DUT:
  module_name: <your_dut_module>
  clock: <clock_signal>
  reset: <reset_signal>
  
  interfaces:
    <interface_1_name>:
      type: <uvc_type>           # istream_env, ostream_env, dpmem_env, etc.
      parameters: [<param1>, <param2>]
      virtual_if: <virtual_if_type>
      
    <interface_2_name>:
      type: <uvc_type>
      parameters: [<param1>]
      virtual_if: <virtual_if_type>
```

### 0.2 Parse Model.cpp (C Reference Model)

**Input:** `model.cpp`

**Process:**
```
Model.cpp
    │
    ├──► Find main() function
    │       │
    │       └──► Extract argc check → Get number of arguments
    │
    ├──► Parse usage string
    │       │
    │       └──► Extract argument names and order
    │
    ├──► Identify input files
    │       └── kernel_file, feature_file, psin_file, etc.
    │
    ├──► Identify output files
    │       └── output_file, golden_file, etc.
    │
    ├──► Identify parameters
    │       └── mode, sign, flags (PS_FIRST, PS_MODE, PS_LAST)
    │
    └──► Output: C model command format string
```

**Extraction Algorithm:**
```python
def parse_c_model(cpp_file_path):
    """
    Parse C/C++ reference model to extract command-line interface
    """
    content = read_file(cpp_file_path)
    
    # 1. Find main function
    main_match = re.search(r'int\s+main\s*\([^)]*\)', content)
    
    # 2. Find argc check to determine argument count
    argc_match = re.search(r'if\s*\(\s*argc\s*!=\s*(\d+)\s*\)', content)
    num_args = int(argc_match.group(1)) if argc_match else 0
    
    # 3. Find usage/help string
    usage_match = re.search(r'Usage:[^"]*"([^"]+)"', content)
    
    # 4. Extract argv assignments
    argv_pattern = r'argv\[(\d+)\]'
    argv_matches = re.findall(argv_pattern, content)
    
    # 5. Build command format
    return {
        'executable': extract_exe_name(cpp_file_path),
        'num_args': num_args,
        'arg_order': extract_arg_order(content),
        'usage_string': usage_match.group(1) if usage_match else ''
    }
```

**Example Output:**
```yaml
c_model:
  executable: ./psout_exe
  num_args: 11
  arguments:
    1: kernel_file
    2: feature_file
    3: psin_hex32_file
    4: addin_hex32_file
    5: output_file
    6: mode
    7: sign_8b
    8: PS_FIRST
    9: PS_MODE
    10: PS_LAST
  command_template: "./psout_exe {kernel} {feature} {psin} {addin} {output} {mode} {sign} {PS_FIRST} {PS_MODE} {PS_LAST}"
```

### 0.3 Generate Configuration Files

**Output Files:**

#### `config/uvc_mapping.yaml`
```yaml
# Auto-generated UVC mapping for this IP
uvc_types:
  istream_env:
    sequencer: istream_sequencer
    sequence_write: istream_directed_write_sequence
    sequence_read: null
    has_parameters: true
    
  ostream_env:
    sequencer: ostream_sequencer
    sequence_write: null
    sequence_read: ostream_random_burst_read_sequence
    has_parameters: true
    
  dpmem_env:
    sequencer: dpmem_sequencer
    sequence_write: dpmem_directed_write_sequence
    sequence_read: dpmem_directed_read_sequence
    has_parameters: true
    
  spmem_env:
    sequencer: spmem_sequencer
    sequence_write: spmem_directed_write_sequence
    sequence_read: null
    has_parameters: true
    
  regbank_env:
    sequencer: computation_sequencer
    sequence_write: computation_configure_write_seq
    sequence_read: null
    has_parameters: false

# IP-specific interface mapping
interfaces:
  m_feature_buffer_env:
    uvc_type: istream_env
    parameters: [64]
    sequencer_name: seqr_feature_buffer
    
  m_kernel_mem_env:
    uvc_type: dpmem_env
    parameters: [64, 9]
    sequencer_name: seqr_kernel_mem
    
  # ... auto-generated from Block YAML
```

#### `config/settings.yaml`
```yaml
# Auto-generated settings for this IP
ip_name: <extracted_from_block_yaml>
env_class: <ip_name>_env
vseqr_class: <ip_name>_virtual_sequencer
interface_name: <ip_name>_if
package_name: <ip_name>_pkg
scoreboard_class: <ip_name>_scoreboard

clock_signal: <from_block_yaml>
reset_signal: <from_block_yaml>

c_model:
  executable: <from_model_parsing>
  command_format: <from_model_parsing>
  
output_paths:
  ip_infra: output/ip_infra
  tests: output/tests
```

---

## Phase A: IP Infrastructure Generation

This phase generates the base UVM components. Runs **once per IP block**.

### A.1 Generate Environment

**LLM Input:**
- Block YAML content
- UVC mapping configuration
- Example environment file (few-shot)

**LLM Output:** `<ip>_env.sv`

**Key Elements:**
```systemverilog
class <ip>_env extends uvm_env;

  // Sub-environments (from Block YAML interfaces)
  <uvc_type>#(<params>) <interface_name>;  // For each interface
  
  // Virtual sequencer
  <ip>_virtual_sequencer v_seqr;
  
  // Scoreboard
  <ip>_scoreboard scoreboard;

  function void build_phase(uvm_phase phase);
    // Create all sub-environments
    // Get virtual interfaces from config_db
  endfunction

  function void connect_phase(uvm_phase phase);
    // Connect sequencers to virtual sequencer
    // v_seqr.<seqr_name> = <interface>_env.m_agent.m_sequencer;
  endfunction

endclass
```

### A.2 Generate Virtual Sequencer

**LLM Input:**
- Block YAML content
- UVC mapping (for sequencer types)
- Example virtual sequencer file

**LLM Output:** `<ip>_virtual_sequencer.sv`

**Key Elements:**
```systemverilog
class <ip>_virtual_sequencer extends uvm_sequencer;

  // Sequencer handles (CRITICAL: names used in vseq)
  <sequencer_type>#(<params>) seqr_<interface_short_name>;  // For each interface
  
  // Virtual interface
  virtual <ip>_if vif;

endclass
```

**CRITICAL:** The sequencer names defined here are passed to Phase B.

### A.3 Generate Interface

**LLM Input:**
- Block YAML content
- Clock/reset signals
- Example interface file

**LLM Output:** `<ip>_if.sv`

**Key Elements:**
```systemverilog
interface <ip>_if(
  input logic <clock>,
  input logic <reset>
);

  // DUT signals (from block description)
  
  // Clocking block
  clocking cb @(posedge <clock>);
  endclocking

  // Helper tasks for golden data capture
  task capture_output_buffer_exp_data(string file_path);
  endtask

endinterface
```

### A.4 Generate Scoreboard

**LLM Input:**
- Block YAML content
- C model output format
- Example scoreboard file

**LLM Output:** `<ip>_scoreboard.sv`

---

## Phase B: Test Case Generation

This phase generates test files for **each test case** in the Vplan.

### Data Flow: Phase A → Phase B

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE A OUTPUT                                │
├─────────────────────────────────────────────────────────────────┤
│  vseqr_content = """                                            │
│    class <ip>_virtual_sequencer extends uvm_sequencer;          │
│      istream_sequencer#(64)    seqr_feature_buffer;             │
│      dpmem_sequencer#(64,9)    seqr_kernel_mem;                 │
│      ostream_sequencer#(64)    seqr_output_buffer;              │
│      computation_sequencer     seqr_compu;                      │
│      virtual <ip>_if vif;                                       │
│    endclass                                                     │
│  """                                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │  (Passed as context)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE B INPUT                                 │
├─────────────────────────────────────────────────────────────────┤
│  get_vseq_prompt(                                               │
│      tc_config = {...},                                         │
│      example_vseq = "...",                                      │
│      vseqr_class = "<ip>_virtual_sequencer",                    │
│      active_uvcs = [...],                                       │
│      generated_vseqr = vseqr_content,  ◄── FROM PHASE A         │
│      c_model_usage = "..."             ◄── FROM PHASE 0         │
│  )                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### B.1 Generate Test File

**For each test case in Vplan:**

**LLM Input:**
- Test case configuration (tc_id, mode, sign, ps_phase)
- Example test file
- Environment class name
- Virtual sequencer class name

**LLM Output:** `TC_<id>_test.sv`

**Key Elements:**
```systemverilog
class TC_<id>_test extends uvm_test;

  <ip>_env env;
  TC_<id>_vseq vseq_compu;
  virtual <ip>_if vif;

  function void build_phase(uvm_phase phase);
    env = <ip>_env::type_id::create("env", this);
    vseq_compu = TC_<id>_vseq::type_id::create("vseq_...");
    // Get vif from config_db
  endfunction

  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    wait(vif.<reset> == 1);
    vseq_compu.start(env.v_seqr);
    phase.drop_objection(this);
  endtask

endclass
```

### B.2 Generate Virtual Sequence

**For each test case in Vplan:**

**LLM Input:**
- Test case configuration
- Active UVCs list
- **Generated virtual sequencer** (from Phase A)
- **C model command format** (from Phase 0)
- Example vseq file

**LLM Output:** `TC_<id>_vseq.sv`

**Key Elements:**
```systemverilog
class TC_<id>_vseq extends uvm_sequence;

  `uvm_declare_p_sequencer(<ip>_virtual_sequencer)

  // Sequences for active UVCs only
  <sequence_type>#(<params>) seq_<name>;

  task body();
    // 1. Set parameters from test config
    mode = <from_vplan>;
    sign_8b = <from_vplan>;
    PS_FIRST = <from_vplan>;
    
    // 2. Generate stimulus data
    $system("python generate_data.py ...");
    
    // 3. Call C reference model (format from Phase 0)
    $system($sformatf("<c_model_command>", args...));
    
    // 4. Setup golden data capture
    p_sequencer.vif.capture_output_buffer_exp_data(...);
    
    // 5. Execute sequences using CORRECT sequencer names
    seq_feat_wr.size = 16;
    seq_feat_wr.file_path = "...";
    seq_feat_wr.start(p_sequencer.seqr_feature_buffer);  // From Phase A
    
    // 6. Start computation
    // 7. Wait for completion
    // 8. Read and compare output
    
  endtask

endclass
```

---

## Phase C: Package & Integration

### C.1 Generate Package File

**LLM Input:**
- List of generated files
- UVC package dependencies
- Example package file

**LLM Output:** `<ip>_pkg.sv`

```systemverilog
package <ip>_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // Import UVC packages (from Block YAML)
  import istream_pkg::*;
  import ostream_pkg::*;
  import dpmem_pkg::*;
  // ...

  // Include infrastructure files
  `include "<ip>_virtual_sequencer.sv"
  `include "<ip>_scoreboard.sv"
  `include "<ip>_env.sv"

  // Include all test cases (auto-generated list)
  `include "TC_<id1>_vseq.sv"
  `include "TC_<id1>_test.sv"
  `include "TC_<id2>_vseq.sv"
  `include "TC_<id2>_test.sv"
  // ...

endpackage
```

### C.2 Generate Filelist

**Output:** `files.f`

```
// UVM Test Case Generator - Filelist
// Auto-generated

// UVC packages
+incdir+$UVC_HOME/istream/
+incdir+$UVC_HOME/ostream/
+incdir+$UVC_HOME/dpmem/
+incdir+$UVC_HOME/spmem/
+incdir+$UVC_HOME/regbank/

// IP testbench
+incdir+./ip_infra/interface/
+incdir+./ip_infra/env/
+incdir+./ip_infra/virtual_sequencer/
+incdir+./tests/virtual_sequences/
+incdir+./tests/tests/

// Package
./ip_infra/pkg/<ip>_pkg.sv
```

---

## Complete Algorithm (Pseudocode)

```python
def run_pipeline(vplan_path, block_yaml_path, model_cpp_path):
    """
    Main pipeline entry point
    """
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 0: Preprocessing
    # ═══════════════════════════════════════════════════════════════
    
    print("PHASE 0: Preprocessing")
    
    # 0.1 Parse Block YAML
    block_info = parse_block_yaml(block_yaml_path)
    ip_name = block_info['dut']['module_name']
    interfaces = block_info['dut']['interfaces']
    
    # 0.2 Parse C Model
    c_model_info = parse_c_model(model_cpp_path)
    c_model_command = c_model_info['command_template']
    
    # 0.3 Generate Config Files
    uvc_mapping = generate_uvc_mapping(interfaces)
    settings = generate_settings(block_info, c_model_info)
    
    save_yaml(uvc_mapping, "config/uvc_mapping.yaml")
    save_yaml(settings, "config/settings.yaml")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE A: IP Infrastructure
    # ═══════════════════════════════════════════════════════════════
    
    print("PHASE A: IP Infrastructure")
    
    # A.1 Generate Environment
    env_prompt = get_env_prompt(block_info, uvc_mapping, example_env)
    env_content = llm.generate(env_prompt)
    save_file(f"output/ip_infra/env/{ip_name}_env.sv", env_content)
    
    # A.2 Generate Virtual Sequencer
    vseqr_prompt = get_vseqr_prompt(block_info, uvc_mapping, example_vseqr)
    vseqr_content = llm.generate(vseqr_prompt)
    save_file(f"output/ip_infra/virtual_sequencer/{ip_name}_virtual_sequencer.sv", vseqr_content)
    
    # A.3 Generate Interface
    interface_prompt = get_interface_prompt(block_info, example_interface)
    interface_content = llm.generate(interface_prompt)
    save_file(f"output/ip_infra/interface/{ip_name}_if.sv", interface_content)
    
    # A.4 Generate Scoreboard
    scoreboard_prompt = get_scoreboard_prompt(block_info, c_model_info)
    scoreboard_content = llm.generate(scoreboard_prompt)
    save_file(f"output/ip_infra/scoreboard/{ip_name}_scoreboard.sv", scoreboard_content)
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE B: Test Cases
    # ═══════════════════════════════════════════════════════════════
    
    print("PHASE B: Test Cases")
    
    # Parse Vplan
    vplan = parse_vplan_yaml(vplan_path)
    test_cases = vplan['test_cases']
    
    generated_tests = []
    generated_vseqs = []
    
    for tc in test_cases:
        tc_id = tc['TC_ID']
        tc_config = extract_tc_config(tc)
        active_uvcs = tc['Active_UVCs']
        
        # B.1 Generate Test
        test_prompt = get_test_prompt(
            tc_config, 
            example_test,
            env_class=f"{ip_name}_env",
            vseqr_class=f"{ip_name}_virtual_sequencer"
        )
        test_content = llm.generate(test_prompt)
        save_file(f"output/tests/tests/{tc_id}_test.sv", test_content)
        generated_tests.append(f"{tc_id}_test.sv")
        
        # B.2 Generate Virtual Sequence
        vseq_prompt = get_vseq_prompt(
            tc_config,
            example_vseq,
            vseqr_class=f"{ip_name}_virtual_sequencer",
            active_uvcs=active_uvcs,
            generated_vseqr=vseqr_content,    # ◄── FROM PHASE A
            c_model_usage=c_model_command      # ◄── FROM PHASE 0
        )
        vseq_content = llm.generate(vseq_prompt)
        save_file(f"output/tests/virtual_sequences/{tc_id}_vseq.sv", vseq_content)
        generated_vseqs.append(f"{tc_id}_vseq.sv")
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE C: Package & Integration
    # ═══════════════════════════════════════════════════════════════
    
    print("PHASE C: Package & Integration")
    
    # C.1 Generate Package
    package_prompt = get_package_prompt(
        block_info,
        example_package,
        vseq_includes=generated_vseqs,
        test_includes=generated_tests
    )
    package_content = llm.generate(package_prompt)
    save_file(f"output/ip_infra/pkg/{ip_name}_pkg.sv", package_content)
    
    # C.2 Generate Filelist
    filelist = generate_filelist(block_info, generated_tests, generated_vseqs)
    save_file("output/files.f", filelist)
    
    print("COMPLETE!")
    return {
        'ip_infra': [...],
        'tests': generated_tests,
        'vseqs': generated_vseqs
    }
```

---

## Applying to a New IP Block

### Step 1: Create Block YAML

```yaml
# my_new_ip/block_description.yaml
DUT:
  module_name: my_new_ip_top
  clock: clk
  reset: rst_n
  
  interfaces:
    m_input_env:
      type: istream_env
      parameters: [32]
      virtual_if: istream_if#(32)
      
    m_output_env:
      type: ostream_env
      parameters: [32]
      virtual_if: ostream_if#(32)
      
    m_config_env:
      type: regbank_env
      virtual_if: regbank_if
```

### Step 2: Create Vplan YAML

```yaml
# my_new_ip/vplan.yaml
test_cases:
  - TC_ID: TC_BASIC_001
    Active_UVCs:
      - m_input_env
      - m_output_env
      - m_config_env
    Stimulus_Generation:
      regbank_program:
        mode: "00"
        enable: 1
    Coverage_Intent:
      functional:
        - basic_throughput
```

### Step 3: Provide C Reference Model

```cpp
// my_new_ip/golden_model.cpp
int main(int argc, char* argv[]) {
    // argv: input_file output_file mode enable
    if (argc != 5) {
        fprintf(stderr, "Usage: %s input_file output_file mode enable\n", argv[0]);
        return 1;
    }
    // ... implementation
}
```

### Step 4: Run Pipeline

```bash
python run_pipeline.py \
    --vplan my_new_ip/vplan.yaml \
    --block my_new_ip/block_description.yaml \
    --model my_new_ip/golden_model.cpp \
    --output my_new_ip/output/
```

### Step 5: Generated Output

```
my_new_ip/output/
├── ip_infra/
│   ├── env/my_new_ip_top_env.sv
│   ├── virtual_sequencer/my_new_ip_top_virtual_sequencer.sv
│   ├── interface/my_new_ip_top_if.sv
│   ├── scoreboard/my_new_ip_top_scoreboard.sv
│   └── pkg/my_new_ip_top_pkg.sv
├── tests/
│   ├── tests/TC_BASIC_001_test.sv
│   └── virtual_sequences/TC_BASIC_001_vseq.sv
└── files.f
```

---

## Key Design Principles

### 1. Model Agnostic
- No hardcoded IP-specific names
- All names derived from Block YAML
- C model format auto-extracted

### 2. Phase Dependencies
```
Phase 0 ──► Phase A ──► Phase B ──► Phase C
   │           │           │
   │           │           └── Uses vseqr_content from A
   │           └── Uses config from 0
   └── Generates config for all phases
```

### 3. Single Source of Truth
- Block YAML defines all interfaces
- Vplan defines all test cases
- Model.cpp defines golden reference format

### 4. Few-Shot Learning
- Each LLM call includes example files
- Examples ensure consistent coding style
- Style adapts to your existing codebase

---

## Summary

| Phase | Input | Output | Runs |
|-------|-------|--------|------|
| **Phase 0** | Block YAML, Model.cpp | Config files | Once per IP |
| **Phase A** | Block YAML, Config, Examples | Infrastructure files | Once per IP |
| **Phase B** | Vplan, Config, Phase A output | Test files | Per test case |
| **Phase C** | All generated files | Package, Filelist | Once per IP |

**Total LLM Calls per IP:**
- Phase 0: 0 (pure parsing)
- Phase A: 4 (env, vseqr, interface, scoreboard)
- Phase B: 2 × N (test + vseq per test case)
- Phase C: 1 (package)

**Formula:** `5 + 2N` LLM calls for N test cases
