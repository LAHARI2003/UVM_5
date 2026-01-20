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
│  ║  [0.2] Parse Model.cpp  → output details_model.txt     ║  │
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


It parses all the UVC components and the `block.yaml` file and makes and config files 
like the uvc_mapping.yaml for the with the detail of ip spefic inteface mappings and the uvcs

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
    └──► Output:  a txt file 



## Phase A: IP Infrastructure Generation

This phase generates the base UVM components. Runs **once per IP block**.

It has to follow the below order because there is dependence in the files (see the example files i have provided you will understand)

### A.1  Generate Interface

**LLM Input:**
- Block YAML content
- Clock/reset signals
- Example interface file

**LLM Output:** `<ip>_if.sv`


### A.2 Generate Virtual Sequencer

**LLM Input:**
- Block YAML content
- UVC mapping (for sequencer types)
- Example virtual sequencer file

**LLM Output:** `<ip>_virtual_sequencer.sv`

### A.3 Generate Environment

**LLM Input:**
- Block YAML content
- UVC mapping configuration
- Example environment file (few-shot)

**LLM Output:** `<ip>_env.sv`


### A.4 Generate Scoreboard

**LLM Input:**
- Block YAML content
- C model output format
- Example scoreboard file

**LLM Output:** `<ip>_scoreboard.sv`


## Phase B: Test Case Generation

This phase generates test files for **each test case** in the Vplan.

### Data Flow: Phase A → Phase B

All the required information has to go from A to B , see the example files for clarity
you will understand.


### B.1 Generate Test File

**For each test case in Vplan:**  VPLAN_FILE



**LLM Output:** `TC_<id>_test.sv`



### B.2 Generate Virtual Sequence

**For each test case in Vplan:**

**LLM Output:** `TC_<id>_vseq.sv`


## Phase C: Package & Integration

### C.1 Generate Package File


**LLM Output:** `<ip>_pkg.sv`



## Key Design Principles

### 1. Model Agnostic
- No hardcoded IP-specific names
- All names derived from Block YAML
- C model format auto-extracted

### 2. Single Source of Truth
- Block YAML defines all interfaces
- Vplan defines all test cases
- Model.cpp defines golden reference format

### 4. Few-Shot Learning
- Each LLM call includes example files
- Examples ensure consistent coding style
- Style adapts to your existing codebase