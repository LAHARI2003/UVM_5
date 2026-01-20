# UVM Test Case Generator Pipeline

A **model-agnostic** pipeline for generating complete UVM testbenches using OpenAI's LLM.

## Overview

This tool automatically generates UVM verification environments from three inputs:
1. **Vplan YAML** - Verification plan with test case definitions
2. **Block YAML** - IP block description (interfaces, clocks, resets)
3. **Model.cpp** - C++ golden reference model

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INPUT FILES                                  │
│  Vplan.yaml  +  Block_YAML_file.txt  +  model.cpp               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 0: Preprocessing                                          │
│  - Parse Block YAML → Extract interfaces, clock/reset            │
│  - Parse Vplan → Extract test cases, stimulus config             │
│  - Parse Model.cpp → Extract arguments, I/O files                │
│  - Generate UVC mapping configuration                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE A: IP Infrastructure (LLM Generation)                     │
│  - Generate Interface (<ip>_if.sv)                               │
│  - Generate Virtual Sequencer (<ip>_virtual_sequencer.sv)        │
│  - Generate Environment (<ip>_env.sv)                            │
│  - Generate Scoreboard (<ip>_scoreboard.sv)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE B: Test Case Generation (LLM Generation)                  │
│  For each test case in Vplan:                                    │
│  - Generate Test File (TC_<id>_test.sv)                          │
│  - Generate Virtual Sequence (TC_<id>_vseq.sv)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE C: Package & Integration (LLM Generation)                 │
│  - Generate Package File (<ip>_pkg.sv)                           │
│  - Generate File List (files.f)                                  │
│  - Generate Testbench Template (<ip>_tb.sv)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OUTPUT FILES                                 │
│  generated/                                                      │
│  ├── ip/                  # Infrastructure files                 │
│  ├── tests/               # Test case files                      │
│  ├── <ip>_pkg.sv          # Package file                         │
│  ├── <ip>_tb.sv           # Testbench                            │
│  └── files.f              # Compilation file list                │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Set your OpenAI API key:

```bash
# Option 1: Environment variable
export OPENAI_API_KEY='your-api-key-here'

# Option 2: Create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

## Usage

### Basic Usage

```bash
python main.py \
    --vplan ../Golden_reference_files/model_files/Vplan.yaml \
    --block ../Golden_reference_files/model_files/Block_YAML_file.txt \
    --model ../Golden_reference_files/model_files/psout_ac_fixed_14_11_25.cpp \
    --output ./generated
```

### All Options

```bash
python main.py --help

Options:
  -v, --vplan PATH      Path to Vplan YAML file
  -b, --block PATH      Path to Block YAML file
  -m, --model PATH      Path to C++ reference model
  -o, --output PATH     Output directory for generated files
  -u, --uvc-path PATH   Path to UVC library
  -g, --golden-ref PATH Path to golden reference files
  --no-scoreboard       Skip scoreboard generation
  --no-package          Skip package file generation
  --verbose             Enable verbose output
  --dry-run             Parse inputs only, do not generate files
```

### Dry Run (Test Configuration)

```bash
python main.py --dry-run
```

## Project Structure

```
uvm_gen_pipeline/
├── main.py                 # CLI and orchestrator
├── config.py               # Configuration management
├── llm_client.py           # OpenAI LLM client
├── parsers.py              # Input file parsers
├── prompts.py              # LLM prompt templates
├── phase0_preprocess.py    # Phase 0: Preprocessing
├── phase_a_infrastructure.py  # Phase A: IP infrastructure
├── phase_b_testgen.py      # Phase B: Test generation
├── phase_c_package.py      # Phase C: Package & integration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Input File Formats

### Vplan.yaml

```yaml
- TC_ID: TC_S2_SF_MODE00_PS_FIRST_K0F0
  Active_UVCs:
    - m_register_env
    - m_kernel_mem_env
    - m_feature_buffer_env
  Stimulus_Generation:
    - regbank_program:
        mode: "00"
        sign_8b: "dont_care"
        ps_phase: "PS_FIRST"
    - input_provisioning:
        kernels:
          target: kernels
          pattern_bin: BIN_K_ALL0
  Coverage_Intent:
    - config_bins: [BIN_MODE_00, BIN_PS_FIRST]
```

### Block_YAML_file.txt

```
Block : 
Name : dimc_tile_wrapper_m 

Clocks : 
  name : clk 
  Frequency : 100Mhz 

Resets : 
  Name : resetn 
  Active_low : true 

Interfaces : 
  Name : m_feature_buffer_env 
  Kind : istream_env#(64) 
  params : { DATA_WIDTH : 64 } 
  Map_to_model : arg : feature 
```

## Few-Shot Learning

The pipeline uses example files from `Golden_reference_files/` as templates:
- Example test files for test generation style
- Example environment files for infrastructure style
- Example interface files for signal naming conventions

## Customization

### Adding New UVC Types

Edit `parsers.py` → `get_sequence_types()` to map new UVC types to their sequences.

### Modifying Prompts

Edit `prompts.py` to customize the LLM prompts for different generation styles.

### Changing LLM Model

Set environment variable:
```bash
export OPENAI_MODEL=gpt-4o
```

## Troubleshooting

### API Key Issues
```
Error: OPENAI_API_KEY environment variable not set!
```
→ Set your API key as shown in Configuration section

### File Not Found
```
Error: Block YAML file not found
```
→ Check file paths, use absolute paths if needed

### Rate Limiting
The pipeline includes automatic retry logic for API rate limits.

## License

Internal use only.
