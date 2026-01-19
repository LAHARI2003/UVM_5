# UVM Test Case Generator - Complete Workflow Details

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Input Files](#input-files)
4. [Phase A: IP Infrastructure Generation](#phase-a-ip-infrastructure-generation)
5. [Phase B: Test Case Generation](#phase-b-test-case-generation)
6. [Data Flow Between Phases](#data-flow-between-phases)
7. [Prompt Engineering](#prompt-engineering)
8. [Output Structure](#output-structure)
9. [Running the Pipeline](#running-the-pipeline)
10. [Key Implementation Details](#key-implementation-details)

---

## 1. Overview

This pipeline automatically generates UVM (Universal Verification Methodology) test cases from YAML-based verification plans. It uses Large Language Models (LLMs) to generate SystemVerilog code that is compatible with Xcelium simulation.

### Goals
- Generate compilable UVM test files (`_test.sv` and `_vseq.sv`)
- Generate IP infrastructure files (environment, virtual sequencer, interface, package)
- Match existing coding style and conventions
- Support multiple test cases from a single vplan YAML

### Pipeline Flow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INPUT FILES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Block_YAML_file.txt   │  sc_2_gpt_5_2.yaml   │  Example Files              │
│  (DUT description)     │  (Verification Plan) │  (env, vseqr, interface)    │
└─────────────┬───────────────────┬─────────────────────┬─────────────────────┘
              │                   │                     │
              ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE A: IP Infrastructure                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  [1] Environment         → p18_dimc_tile_wrap_env.sv                        │
│  [2] Virtual Sequencer   → p18_dimc_tile_wrap_virtual_sequencer.sv          │
│  [3] Interface           → dimc_tilewrap_if.sv                              │
│  [4] Package             → dimc_tile_wrap_pkg.sv                            │
└─────────────┬───────────────────────────────────────────────────────────────┘
              │
              │ (Pass generated virtual sequencer as context)
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE B: Test Cases                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  For each test case in vplan:                                               │
│    [1] Generate _test.sv  (UVM test class)                                  │
│    [2] Generate _vseq.sv  (Virtual sequence)                                │
└─────────────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT FILES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  output/                                                                     │
│  ├── ip_infra/                                                              │
│  │   ├── env/p18_dimc_tile_wrap_env.sv                                      │
│  │   ├── virtual_sequencer/p18_dimc_tile_wrap_virtual_sequencer.sv          │
│  │   ├── interface/dimc_tilewrap_if.sv                                      │
│  │   └── pkg/dimc_tile_wrap_pkg.sv                                          │
│  └── tests/                                                                 │
│      ├── tests/TC_xxx_test.sv                                               │
│      └── virtual_sequences/TC_xxx_vseq.sv                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture

### Directory Structure
```
uvm_generator/
├── run_with_openai.py          # Main entry point
├── env_config.txt              # API key configuration
├── WORKFLOW_DETAILS.md         # This document
├── config/                     # Configuration files
│   ├── settings.yaml
│   └── uvc_mapping.yaml
├── prompts/                    # LLM prompt templates
│   ├── ip_infra_prompts.py     # Phase A prompts
│   └── test_case_prompts.py    # Phase B prompts
├── utils/                      # Utility modules
│   ├── parser.py               # YAML parsers
│   ├── llm_client.py           # LLM API client
│   └── file_utils.py           # File operations
└── output/                     # Generated files
    ├── ip_infra/
    └── tests/
```

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| Main Pipeline | `run_with_openai.py` | Orchestrates the entire generation flow |
| Block Parser | `utils/parser.py` | Parses Block_YAML_file.txt for DUT info |
| Vplan Parser | `utils/parser.py` | Parses vplan YAML for test cases |
| LLM Client | `utils/llm_client.py` | Handles API calls to OpenAI/Anthropic |
| File Manager | `utils/file_utils.py` | Manages output file writing |
| IP Infra Prompts | `prompts/ip_infra_prompts.py` | Templates for Phase A |
| Test Case Prompts | `prompts/test_case_prompts.py` | Templates for Phase B |

---

## 3. Input Files

### 3.1 Block YAML File (`model_files/Block_YAML_file.txt`)

Describes the DUT (Device Under Test) and its interfaces.

```yaml
DUT:
  module_name: dimc_tile_wrapper_m
  clock: dimc_tilewrap_clk
  reset: resetn
  
  reference_model:
    type: C_model
    path: ./psout_ac_fixed_14_11_25.cpp
    executable: ./psout_exe
    
  interfaces:
    m_feature_buffer_env:
      type: istream_env
      parameters: [64]
      virtual_if: istream_if#(64)
      
    m_kernel_mem_env:
      type: dpmem_env
      parameters: [64, 9]
      virtual_if: dpmem_if#(64,9)
      
    m_psin_env:
      type: istream_env
      parameters: [32]
      virtual_if: istream_if#(32)
      
    m_addin_env:
      type: spmem_env
      parameters: [64, 4]
      virtual_if: spmem_if#(64,4)
      
    m_computation_env:
      type: regbank_env
      virtual_if: regbank_if
      
    m_output_buffer_env:
      type: ostream_env
      parameters: [64]
      virtual_if: ostream_if#(64)
```

### 3.2 Verification Plan YAML (`model_files/sc_2_gpt_5_2.yaml`)

Defines test cases with their configurations.

```yaml
test_cases:
  - TC_ID: TC_S2_SF_MODE00_PS_FIRST_K0F0
    Active_UVCs:
      - m_feature_buffer_env
      - m_kernel_mem_env
      - m_addin_env
      - m_computation_env
      - m_output_buffer_env
    
    Stimulus_Generation:
      regbank_program:
        mode: "00"           # 1-bit mode (0-3)
        sign_8b: "dont_care" # Sign configuration
        ps_phase: "PS_FIRST" # Partial sum phase
      
      input_provisioning:
        pattern_bin: random
        
    Observability:
      signals:
        - psout_buff_full
        
    Coverage_Intent:
      functional:
        - basic_operation_mode0
```

### 3.3 Example Files (`OTHER REQUIRED FILES/`)

These files serve as few-shot examples for the LLM:

| File | Purpose |
|------|---------|
| `env/p18_dimc_tile_wrap_env.sv` | Example environment class |
| `virtual_sequencer/p18_dimc_tile_wrap_virtual_sequencer.sv` | Example virtual sequencer |
| `interface/dimc_tile_wrap_if_interface.sv` | Example DUT interface |
| `pkg/dimc_tile_wrap_package.sv` | Example package file |

### 3.4 Reference Test Files (`Test_case_File/`)

Golden reference test files for style matching:

| File | Purpose |
|------|---------|
| `CI_TC_005_mode0_sign0_PS_FIRST_test.sv` | Example _test.sv |
| `CI_TC_005_mode0_sign0_PS_FIRST_vseq.sv` | Example _vseq.sv |

---

## 4. Phase A: IP Infrastructure Generation

Phase A generates the base UVM components for the IP block.

### 4.1 Environment Generation (`p18_dimc_tile_wrap_env.sv`)

**Prompt Function:** `get_env_prompt()`

**Inputs:**
- Block YAML content
- Example environment file
- Environment class name
- Virtual sequencer class name

**Generated Content:**
```systemverilog
class p18_dimc_tile_wrap_env extends uvm_env;

  // Sub-environment instances (from Block YAML interfaces)
  istream_env#(64)    m_feature_buffer_env;
  dpmem_env#(64,9)    m_kernel_mem_env;
  ostream_env#(64)    m_output_buffer_env;
  istream_env#(32)    m_psin_env;
  spmem_env#(64,4)    m_addin_env;
  regbank_env         m_computation_env;

  // Virtual sequencer
  p18_dimc_tile_wrap_virtual_sequencer v_seqr;
  
  // Scoreboard
  p18_dimc_tile_wrap_scoreboard#(64) dimc_tile_wrap_scoreboard;

  // build_phase: Create all components
  function void build_phase(uvm_phase phase);
    // Create sub-environments
    // Get virtual interfaces from config_db
  endfunction

  // connect_phase: Connect sequencers to virtual sequencer
  function void connect_phase(uvm_phase phase);
    v_seqr.seqr_feature_buffer = m_feature_buffer_env.m_agent.m_sequencer;
    v_seqr.seqr_kernel_mem     = m_kernel_mem_env.m_agent.m_sequencer;
    // ... etc
  endfunction

endclass
```

### 4.2 Virtual Sequencer Generation (`p18_dimc_tile_wrap_virtual_sequencer.sv`)

**Prompt Function:** `get_virtual_sequencer_prompt()`

**Generated Content:**
```systemverilog
class p18_dimc_tile_wrap_virtual_sequencer extends uvm_sequencer;

  `uvm_component_utils(p18_dimc_tile_wrap_virtual_sequencer)

  // Sequencer handles (CRITICAL: These names are used in _vseq.sv)
  istream_sequencer#(64)    seqr_feature_buffer;
  dpmem_sequencer#(64,9)    seqr_kernel_mem;
  ostream_sequencer#(64)    seqr_output_buffer;
  istream_sequencer#(32)    seqr_psin;
  spmem_sequencer#(64,4)    seqr_addin;
  computation_sequencer     seqr_compu;

  // Virtual interface for DUT access
  virtual dimc_tilewrap_if vif;

endclass
```

**CRITICAL:** The sequencer names defined here (`seqr_feature_buffer`, `seqr_compu`, etc.) MUST be used in Phase B's virtual sequence files.

### 4.3 Interface Generation (`dimc_tilewrap_if.sv`)

**Prompt Function:** `get_interface_prompt()`

**Generated Content:**
```systemverilog
interface dimc_tilewrap_if(
  input logic dimc_tilewrap_clk,
  input logic resetn
);

  // DUT signals
  logic psout_buff_full;
  logic [63:0] output_data;
  // ... other signals

  // Clocking block
  clocking cb @(posedge dimc_tilewrap_clk);
    // Signal directions
  endclocking

  // Modport for driver
  modport drv(clocking cb);
  
  // Modport for monitor
  modport mon(clocking cb);

  // Helper tasks
  task capture_output_buffer_exp_data(string file_path);
    // Load golden data for comparison
  endtask

endinterface
```

### 4.4 Package Generation (`dimc_tile_wrap_pkg.sv`)

**Prompt Function:** `get_package_prompt()`

**Generated Content:**
```systemverilog
package dimc_tile_wrap_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // Import UVC packages
  import istream_pkg::*;
  import dpmem_pkg::*;
  import ostream_pkg::*;
  import spmem_pkg::*;
  import regbank_pkg::*;

  // Include local files
  `include "p18_dimc_tile_wrap_virtual_sequencer.sv"
  `include "p18_dimc_tile_wrap_scoreboard.sv"
  `include "p18_dimc_tile_wrap_env.sv"

  // Include test cases
  `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv"
  `include "TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv"

endpackage
```

---

## 5. Phase B: Test Case Generation

Phase B generates individual test cases based on the vplan.

### 5.1 Test File Generation (`TC_xxx_test.sv`)

**Prompt Function:** `get_test_prompt()`

**Input Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| `tc_id` | Test case identifier | `TC_S2_SF_MODE00_PS_FIRST_K0F0` |
| `mode` | Operation mode | `00`, `01`, `10`, `11` |
| `sign_8b` | Sign configuration | `00`, `01`, `10`, `11`, `dont_care` |
| `ps_phase` | Partial sum phase | `PS_FIRST`, `PS_MODE`, `PS_LAST` |

**Generated Structure:**
```systemverilog
class TC_S2_SF_MODE00_PS_FIRST_K0F0_test extends uvm_test;

  `uvm_component_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_test)

  // Declarations
  p18_dimc_tile_wrap_env env;
  TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq vseq_compu;
  virtual dimc_tilewrap_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = p18_dimc_tile_wrap_env::type_id::create("env", this);
    vseq_compu = TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq::type_id::create(
      $sformatf("vseq_mode%0d_sign%0d", 0, 0)
    );
    
    // Get virtual interface
    if (!uvm_config_db#(virtual dimc_tilewrap_if)::get(this, "", "dimc_tilewrap_vif", vif))
      `uvm_fatal("NOVIF", "Virtual interface not set")
  endfunction

  task run_phase(uvm_phase phase);
    phase.raise_objection(this);
    
    wait(vif.resetn == 1);
    repeat(5) @(vif.cb);
    
    vseq_compu.start(env.v_seqr);
    
    repeat(10) @(vif.cb);
    phase.drop_objection(this);
  endtask

endclass
```

### 5.2 Virtual Sequence Generation (`TC_xxx_vseq.sv`)

**Prompt Function:** `get_vseq_prompt()`

**CRITICAL Input: Generated Virtual Sequencer**

The generated virtual sequencer from Phase A is passed to Phase B to ensure correct sequencer names:

```python
vseq_prompt = get_vseq_prompt(
    tc_config=tc_config,
    example_vseq=examples.get('vseq', ''),
    vseqr_class=vseqr_class_name,
    active_uvcs=tc.get('Active_UVCs', []),
    uvc_mapping={},
    generated_vseqr=vseqr_content,  # <-- CRITICAL: Pass Phase A output
    c_model_usage=""
)
```

**Generated Structure:**
```systemverilog
class TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq extends uvm_sequence;

  `uvm_object_utils(TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq)
  `uvm_declare_p_sequencer(p18_dimc_tile_wrap_virtual_sequencer)

  // Sequences (ONLY for active UVCs)
  istream_directed_write_sequence#(64)    seq_feat_wr;
  dpmem_directed_write_sequence#(64,9)    seq_ker_wr;
  spmem_directed_write_sequence#(64,4)    seq_addin_wr;
  computation_configure_write_seq         seq_compu_wr;
  ostream_random_burst_read_sequence#(64) seq_outbuf_rd;

  // Variables
  int mode, feature_buffer_size, sign_8b, PS_FIRST, PS_MODE, PS_LAST;

  task body();
    // a. Set parameters
    mode = 0;
    sign_8b = 0;
    PS_FIRST = 1;
    PS_MODE = 0;
    PS_LAST = 0;

    // b. Generate stimulus data
    $system($sformatf("python generate_data_hex_unique.py %0d %0d %0d", 
                       mode, feature_buffer_size, sign_8b));

    // c. Call C reference model (EXACT format)
    $system($sformatf("./psout_exe %s %s %s %s %s %0d %0d %0d %0d %0d",
                      kernel_file, feature_file, psin_file, addin_file, output_file,
                      mode, sign_8b, PS_FIRST, PS_MODE, PS_LAST));

    // d. Setup capture
    p_sequencer.vif.capture_output_buffer_exp_data(output_file);

    // e. Initialize computation
    seq_compu_wr.START_COMPUTE = 0;
    seq_compu_wr.COMPE = 0;
    seq_compu_wr.start(p_sequencer.seqr_compu);

    // f. Write input data (CRITICAL: Use correct sequencer names)
    seq_feat_wr.size = 16;
    seq_feat_wr.file_path = "./feature_hex_rtl.txt";
    seq_feat_wr.start(p_sequencer.seqr_feature_buffer);  // NOT m_feature_buffer_env

    seq_ker_wr.size = 512;
    seq_ker_wr.file_path = "./kernel_hex_rtl.txt";
    seq_ker_wr.start(p_sequencer.seqr_kernel_mem);

    // g. Start computation
    seq_compu_wr.START_COMPUTE = 1;
    seq_compu_wr.COMPE = 1;
    seq_compu_wr.start(p_sequencer.seqr_compu);

    // h. Wait and read output
    @(posedge p_sequencer.vif.psout_buff_full);
    seq_outbuf_rd.size = 32;
    seq_outbuf_rd.start(p_sequencer.seqr_output_buffer);

  endtask

endclass
```

---

## 6. Data Flow Between Phases

### Critical Data Dependencies

```
Phase A                              Phase B
────────                             ────────
                                     
[1] Generate Environment ───────────────────────────────────────────┐
    └─► env_content                                                 │
                                                                    │
[2] Generate Virtual Sequencer ──┐                                  │
    └─► vseqr_content ───────────┼──────────► get_vseq_prompt() ◄───┤
                                 │            (Uses vseqr_content   │
                                 │             for sequencer names) │
[3] Generate Interface ──────────┘                                  │
    └─► interface_content                                           │
                                                                    │
[4] Generate Package ◄──────────────────────────────────────────────┘
    (Includes all generated files)
```

### Why This Matters

Without passing `vseqr_content` to Phase B, the LLM would generate:
```systemverilog
// WRONG - LLM guesses the path
seq_feat_wr.start(p_sequencer.m_feature_buffer_env.m_sequencer);
```

With `vseqr_content` passed, the LLM generates:
```systemverilog
// CORRECT - Uses actual sequencer names
seq_feat_wr.start(p_sequencer.seqr_feature_buffer);
```

---

## 7. Prompt Engineering

### 7.1 Key Prompt Sections

Each prompt follows this structure:

```
1. ROLE:        "You are a UVM verification expert..."
2. CONTEXT:     Test case configuration, active UVCs, flags
3. EXAMPLES:    Few-shot examples from existing codebase
4. REQUIREMENTS: Numbered, specific instructions
5. OUTPUT:      "Generate ONLY valid SystemVerilog code"
```

### 7.2 Critical Prompt Requirements (from `test_case_prompts.py`)

```python
## CRITICAL Requirements - Follow these EXACTLY:

8. **CRITICAL - Sequencer Access**: Use these EXACT paths:
   - seq_feat_wr.start(p_sequencer.seqr_feature_buffer);
   - seq_ker_wr.start(p_sequencer.seqr_kernel_mem);
   - seq_compu_wr.start(p_sequencer.seqr_compu);

9. **CRITICAL - Sequence Field Assignment**: Use DIRECT assignment:
   CORRECT:
     seq_feat_wr.size = 16;
     seq_feat_wr.file_path = "./feature_hex_rtl.txt";
   
   WRONG (do NOT use):
     seq_feat_wr.randomize() with { size == 16; filename == "..."; }

10. **CRITICAL - Field Names**: 
    - Use 'file_path' (not 'filename')
    - Use 'size' for data size
```

### 7.3 C Reference Model Command Format

The prompt includes exact command format from model inspection:

```
./psout_exe kernel_file feature_file psin_hex32_file addin_hex32_file output_file mode sign_8b PS_FIRST PS_MODE PS_LAST

Arguments (in order):
1. kernel_file      - "./kernel_hex_rtl.txt"
2. feature_file     - "./feature_hex_rtl.txt"
3. psin_hex32_file  - "./psin_hex32_input.txt"
4. addin_hex32_file - "./addin_hex32_input.txt"
5. output_file      - "./golden.txt"
6. mode             - integer (0-3)
7. sign_8b          - integer (0-3)
8. PS_FIRST         - 0 or 1
9. PS_MODE          - 0 or 1
10. PS_LAST         - 0 or 1
```

---

## 8. Output Structure

### Directory Layout
```
uvm_generator/output/
├── ip_infra/
│   ├── env/
│   │   └── p18_dimc_tile_wrap_env.sv
│   ├── virtual_sequencer/
│   │   └── p18_dimc_tile_wrap_virtual_sequencer.sv
│   ├── interface/
│   │   └── dimc_tilewrap_if.sv
│   └── pkg/
│       └── dimc_tile_wrap_pkg.sv
└── tests/
    ├── tests/
    │   ├── TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv
    │   ├── TC_S2_SF_MODE01_PS_MODE_K1F1_test.sv
    │   └── ... (one per test case)
    └── virtual_sequences/
        ├── TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv
        ├── TC_S2_SF_MODE01_PS_MODE_K1F1_vseq.sv
        └── ... (one per test case)
```

### File Header Format

All generated files include:
```systemverilog
//═══════════════════════════════════════════════════════════════════════════════
// File: <filename>.sv
// Auto-generated by UVM Generator
// Generated: YYYY-MM-DD HH:MM:SS
// 
// WARNING: This file is auto-generated. Manual changes may be overwritten.
//═══════════════════════════════════════════════════════════════════════════════
```

---

## 9. Running the Pipeline

### 9.1 Prerequisites

1. **Python 3.8+**
2. **OpenAI API Key**
3. **Required packages:** `openai`, `pyyaml`

### 9.2 Configuration

Edit `env_config.txt`:
```
OPENAI_API_KEY=sk-proj-your-api-key-here
```

### 9.3 Execution

```powershell
cd C:\office\UVM_Test_Case_gen\uvm_generator
python run_with_openai.py
```

### 9.4 Expected Output

```
============================================================
UVM Generator - OpenAI GPT Run
============================================================

Loading API key from env_config.txt...
  Loaded: OPENAI_API_KEY=sk-proj-yK...
  API Key loaded: sk-proj-yKkbYTp...

Configuration:
  Block YAML:  ...\model_files\Block_YAML_file.txt
  Vplan YAML:  ...\Test_case_File\example.yaml
  Examples:    ...\OTHER REQUIRED FILES
  Output:      ...\uvm_generator\output

============================================================
PHASE A: Generating IP Infrastructure
============================================================

[1/3] Generating Environment...
  [OK] Created: ...\ip_infra\env\p18_dimc_tile_wrap_env.sv

[2/3] Generating Virtual Sequencer...
  [OK] Created: ...\ip_infra\virtual_sequencer\p18_dimc_tile_wrap_virtual_sequencer.sv

[3/3] Generating Interface...
  [OK] Created: ...\ip_infra\interface\dimc_tilewrap_if.sv

[OK] Phase A complete!

============================================================
PHASE B: Generating Test Cases
============================================================

[1/1] Generating: TC_S2_SF_MODE00_PS_FIRST_K0F0
  Config: mode=00, sign=dont_care, ps=PS_FIRST
  Generating _test.sv...
    [OK] TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv
  Generating _vseq.sv...
    [OK] TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv

[OK] Phase B complete! Generated 1 test cases

============================================================
Generating Package File
============================================================
  [OK] Created: ...\ip_infra\pkg\dimc_tile_wrap_pkg.sv

============================================================
GENERATION COMPLETE
============================================================
```

---

## 10. Key Implementation Details

### 10.1 LLM Client Configuration

```python
# utils/llm_client.py

class LLMClient:
    def __init__(self, provider="openai", api_key=None, model="gpt-5.2-2025-12-11"):
        self.provider = provider
        self.model = model
        
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
    
    def generate(self, prompt: str) -> str:
        # Use max_completion_tokens for newer models
        if "gpt-5" in self.model or "gpt-4.1" in self.model:
            params = {"max_completion_tokens": 4096}
        else:
            params = {"max_tokens": 4096}
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Low temperature for consistent code
            **params
        )
        return response.choices[0].message.content
```

### 10.2 File Utilities

```python
# utils/file_utils.py

class FileManager:
    def write_file(self, relative_path: str, content: str) -> str:
        # Add header to generated files
        header = self._generate_header(relative_path)
        full_content = header + self._clean_content(content)
        
        # Ensure UTF-8 encoding for Windows compatibility
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
```

### 10.3 YAML Parsers

```python
# utils/parser.py

class VplanYAMLParser:
    def get_test_cases(self) -> list:
        """Return list of test case dictionaries"""
        return self.data.get('test_cases', [])
    
    def extract_config(self, tc: dict) -> dict:
        """Extract configuration from test case"""
        stimulus = tc.get('Stimulus_Generation', {})
        regbank = stimulus.get('regbank_program', {})
        
        return {
            'tc_id': tc.get('TC_ID'),
            'mode': regbank.get('mode', '00'),
            'sign_8b': regbank.get('sign_8b', 'dont_care'),
            'ps_phase': regbank.get('ps_phase', 'PS_FIRST')
        }
```

### 10.4 Mode/Sign Mapping

| Mode String | Integer Value | Bits |
|-------------|---------------|------|
| `"00"` | 0 | 8-bit |
| `"01"` | 1 | 4-bit |
| `"10"` | 2 | 2-bit |
| `"11"` | 3 | 1-bit |

| Sign String | Integer Value |
|-------------|---------------|
| `"dont_care"` | 0 |
| `"00"` | 0 |
| `"01"` | 1 |
| `"10"` | 2 |
| `"11"` | 3 |

| PS Phase | PS_FIRST | PS_MODE | PS_LAST |
|----------|----------|---------|---------|
| `PS_FIRST` | 1 | 0 | 0 |
| `PS_MODE` | 0 | 1 | 0 |
| `PS_LAST` | 0 | 0 | 1 |

---

## Appendix A: Common Issues and Solutions

### Issue 1: Wrong Sequencer Names in vseq

**Symptom:**
```systemverilog
seq_feat_wr.start(p_sequencer.m_feature_buffer_env.m_sequencer);
```

**Solution:** Pass generated virtual sequencer to Phase B prompt:
```python
vseq_prompt = get_vseq_prompt(
    ...
    generated_vseqr=vseqr_content,  # <-- Add this
)
```

### Issue 2: Wrong Field Names

**Symptom:**
```systemverilog
seq_feat_wr.filename = "...";  // Wrong
```

**Solution:** Add explicit requirements in prompt:
```
Use 'file_path' (not 'filename')
```

### Issue 3: UnicodeEncodeError on Windows

**Symptom:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'
```

**Solution:** Use UTF-8 encoding:
```python
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
```

### Issue 4: OpenAI max_tokens Error

**Symptom:**
```
Unsupported parameter: 'max_tokens' is not supported with this model
```

**Solution:** Use `max_completion_tokens` for newer models:
```python
if "gpt-5" in model or "gpt-4.1" in model:
    params = {"max_completion_tokens": 4096}
else:
    params = {"max_tokens": 4096}
```

---

## Appendix B: Extending the Pipeline

### Adding a New UVC Type

1. Update `Block_YAML_file.txt` with new interface
2. Add mapping in `config/uvc_mapping.yaml`
3. Update prompt templates if special handling needed

### Adding New Test Case Parameters

1. Add to vplan YAML structure
2. Update `VplanYAMLParser.extract_config()`
3. Update `get_vseq_prompt()` with new parameter handling

### Customizing Code Style

Edit the example files in `OTHER REQUIRED FILES/` - the LLM uses these as few-shot examples.

---

## Appendix C: Future Enhancements

1. **C Model Auto-Inspection**: Automatically parse C++ model for command format
2. **Syntax Validation**: Run Xcelium lint on generated files
3. **Batch Processing**: Generate all 21 test cases in parallel
4. **Coverage Tracking**: Generate functional coverage based on Coverage_Intent
5. **Interactive Mode**: Ask user for clarification on ambiguous cases
