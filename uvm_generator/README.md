# UVM Generator - LLM-Powered UVM Test Case Generation

An automated pipeline that generates UVM test environments and test cases using Large Language Models (LLMs).

## Overview

This tool transforms verification plans (YAML specifications) into compilable UVM SystemVerilog code:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│   Block YAML    │     │   Vplan YAML    │     │    Generated UVM        │
│ (IP Description)│ ──► │ (Test Cases)    │ ──► │  - Environment          │
│                 │     │                 │     │  - Virtual Sequencer    │
│                 │     │                 │     │  - Test Cases           │
└─────────────────┘     └─────────────────┘     └─────────────────────────┘
```

## Features

- **Phase A**: Generate IP infrastructure (env, virtual_sequencer, interface, package)
- **Phase B**: Generate test cases (_test.sv, _vseq.sv) from vplan
- **LLM-powered**: Uses Claude or GPT-4 for intelligent code generation
- **Few-shot learning**: Uses example files for consistent output
- **Xcelium compatible**: Generates compilable SystemVerilog

## Installation

```bash
# Clone or copy to your workspace
cd uvm_generator

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### API Key Setup

Set your LLM API key as an environment variable:

```bash
# For Anthropic (Claude)
export ANTHROPIC_API_KEY="your-api-key"

# For OpenAI (GPT-4)
export OPENAI_API_KEY="your-api-key"
```

Or pass it via command line: `--api-key "your-api-key"`

### Configuration Files

- `config/settings.yaml` - LLM settings, output paths, naming conventions
- `config/uvc_mapping.yaml` - UVC to sequence type mappings

## Usage

### Generate Everything (Recommended)

```bash
python generate_uvm.py \
    --block ../model_files/Block_YAML_file.txt \
    --vplan ../model_files/sc_2_gpt_5_2.yaml \
    --output ./output \
    --examples "../OTHER REQUIRED FILES" \
    --uvc-lib ../uvc
```

### Generate Only Infrastructure (Phase A)

```bash
python generate_uvm.py \
    --block ../model_files/Block_YAML_file.txt \
    --vplan ../model_files/sc_2_gpt_5_2.yaml \
    --output ./output \
    --phase-a-only
```

### Generate Only Test Cases (Phase B)

```bash
python generate_uvm.py \
    --block ../model_files/Block_YAML_file.txt \
    --vplan ../model_files/sc_2_gpt_5_2.yaml \
    --output ./output \
    --phase-b-only
```

### Generate Specific Test Cases

```bash
python generate_uvm.py \
    --block ../model_files/Block_YAML_file.txt \
    --vplan ../model_files/sc_2_gpt_5_2.yaml \
    --output ./output \
    --test-ids TC_S2_SF_MODE00_PS_FIRST_K0F0 TC_S2_SF_MODE01_PS_MODE_KRFR_PSINP_AD0
```

### Use OpenAI Instead of Anthropic

```bash
python generate_uvm.py \
    --block ../model_files/Block_YAML_file.txt \
    --vplan ../model_files/sc_2_gpt_5_2.yaml \
    --output ./output \
    --provider openai \
    --model gpt-4-turbo
```

## Output Structure

```
output/
├── ip_infra/
│   ├── env/
│   │   └── p18_dimc_tile_wrap_env.sv
│   ├── interface/
│   │   └── dimc_tilewrap_if.sv
│   ├── virtual_sequencer/
│   │   └── p18_dimc_tile_wrap_virtual_sequencer.sv
│   └── pkg/
│       └── dimc_tile_wrap_pkg.sv
│
└── tests/
    ├── tests/
    │   ├── TC_S2_SF_MODE00_PS_FIRST_K0F0_test.sv
    │   ├── TC_S2_SF_MODE00_PS_MODE_KRFR_PSINP_AD0_test.sv
    │   └── ...
    └── virtual_sequences/
        ├── TC_S2_SF_MODE00_PS_FIRST_K0F0_vseq.sv
        ├── TC_S2_SF_MODE00_PS_MODE_KRFR_PSINP_AD0_vseq.sv
        └── ...
```

## Input Files

### Block YAML (Block_YAML_file.txt)

Describes the IP/DUT being verified:

```yaml
Block:
Name: dimc_tile_wrapper_m

Clocks:
  name: clk
  Frequency: 100Mhz

Resets:
  Name: resetn
  Active_low: true

Interfaces:
  Name: m_feature_buffer_env
  Kind: istream_env#(64)
  params: { DATA_WIDTH: 64 }
  Map_to_model: arg: feature
  # ... more interfaces
```

### Vplan YAML (sc_2_gpt_5_2.yaml)

Contains test case specifications:

```yaml
- TC_ID: TC_S2_SF_MODE00_PS_FIRST_K0F0
  Active_UVCs:
    - m_computation_env
    - m_kernel_mem_env
    - m_feature_buffer_env
    - m_output_buffer_env
  Stimulus_Generation:
    - regbank_program:
        mode: "00"
        sign_8b: "dont_care"
        ps_phase: "PS_FIRST"
    - input_provisioning:
        kernels:
          pattern_bin: BIN_K_ALL0
        feature:
          pattern_bin: BIN_F_ALL0
  # ... more configuration
```

## Pipeline Architecture

```
                        ┌─────────────────────────┐
                        │     Block YAML          │
                        │     Vplan YAML          │
                        │     UVC Library         │
                        │     Example Files       │
                        └───────────┬─────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │    Context Builder      │
                        │  - Parse YAML files     │
                        │  - Collect UVC info     │
                        │  - Load examples        │
                        └───────────┬─────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
              ▼                                           ▼
┌─────────────────────────────┐         ┌─────────────────────────────┐
│      PHASE A                │         │      PHASE B                │
│  IP Infrastructure          │         │  Test Cases                 │
│                             │         │                             │
│  ┌─────────────────────┐    │         │  For each test in vplan:    │
│  │ Generate env.sv     │    │         │  ┌─────────────────────┐    │
│  │ via LLM API call    │    │         │  │ Generate _test.sv   │    │
│  └─────────────────────┘    │         │  │ via LLM API call    │    │
│  ┌─────────────────────┐    │         │  └─────────────────────┘    │
│  │ Generate vseqr.sv   │    │         │  ┌─────────────────────┐    │
│  │ via LLM API call    │    │         │  │ Generate _vseq.sv   │    │
│  └─────────────────────┘    │         │  │ via LLM API call    │    │
│  ┌─────────────────────┐    │         │  └─────────────────────┘    │
│  │ Generate if.sv      │    │         │                             │
│  │ via LLM API call    │    │         │                             │
│  └─────────────────────┘    │         │                             │
└─────────────────────────────┘         └─────────────────────────────┘
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │   Generate Package      │
                        │   with all includes     │
                        └───────────┬─────────────┘
                                    │
                                    ▼
                        ┌─────────────────────────┐
                        │   Output Files          │
                        │   Ready for Xcelium     │
                        └─────────────────────────┘
```

## Troubleshooting

### API Key Issues
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# Set it if not
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Invalid YAML Format
Ensure your YAML files follow the expected format. Check `model_files/` for examples.

## Customization

### Adding New UVC Types

Edit `config/uvc_mapping.yaml` to add new UVC mappings:

```yaml
uvc_mapping:
  m_new_uvc_env:
    env_type: "new_uvc_env#(params)"
    sequencer_type: "new_uvc_sequencer#(params)"
    sequences:
      write: "new_uvc_write_sequence#(params)"
```

### Modifying Prompts

Edit files in `prompts/` directory:
- `ip_infra_prompts.py` - Prompts for Phase A
- `test_case_prompts.py` - Prompts for Phase B

## License

Internal use only.

## Author

Auto-generated pipeline for UVM verification.
