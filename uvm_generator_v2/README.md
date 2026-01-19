# UVM Generator V2

LLM-powered UVM test environment and test case generator - **Generic version** that works with any IP block.

## Key Improvements over V1

| Issue in V1 | Fixed in V2 |
|-------------|-------------|
| Hardcoded class names (`dimc_tilewrap_if`, `dimc_tile_wrap_pkg`) | All names derived from Block YAML |
| Hardcoded interface types in prompts | Dynamic prompts from interface definitions |
| Hardcoded C model command (`psout_exe`) | C model config from Block YAML |
| Rigid YAML parser format | Flexible parser supporting multiple formats |
| Missing scoreboard generation | Scoreboard generation in Phase A.4 |
| Hardcoded UVC mapping | Configurable via `uvc_mapping.yaml` |
| Basic retry (3 attempts) | Exponential backoff with rate limit handling |
| No validation | Basic SystemVerilog validation |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY=your-api-key

# OR for OpenAI
export OPENAI_API_KEY=your-api-key
```

### 3. Prepare Your IP Files

Create these files for your IP:

#### Block YAML (`my_ip/block.yaml`)
```yaml
DUT:
  module_name: my_ip_top
  clock: clk
  reset: rst_n
  
  reference_model:
    type: C_model
    executable: ./my_model
    command_format: "./my_model {input} {output} {mode}"
  
  interfaces:
    m_input_env:
      type: istream_env
      parameters: [64]
    m_output_env:
      type: ostream_env
      parameters: [64]
    m_config_env:
      type: regbank_env
```

#### Vplan YAML (`my_ip/vplan.yaml`)
```yaml
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
```

#### UVC Mapping (`my_ip/uvc_mapping.yaml`)
Copy `config/uvc_mapping_template.yaml` and customize for your interfaces.

### 4. Run Generator

```bash
python generate_uvm.py \
    --block my_ip/block.yaml \
    --vplan my_ip/vplan.yaml \
    --output my_ip/output \
    --uvc-mapping my_ip/uvc_mapping.yaml \
    --examples path/to/example/files
```

## Command Line Options

```
Required:
  --block         Path to Block YAML file
  --vplan         Path to Vplan YAML file
  --output        Output directory

Optional:
  --examples      Path to example files for few-shot learning
  --uvc-lib       Path to UVC library directory
  --uvc-mapping   Path to custom UVC mapping YAML
  --config-dir    Path to config directory (default: ./config)
  --api-key       LLM API key (or use env var)
  --provider      LLM provider: anthropic or openai
  --model         Specific model name

Phase Control:
  --phase-a-only  Only generate infrastructure
  --phase-b-only  Only generate test cases (requires existing infra)
  --test-ids      Specific test IDs to generate (space-separated)
  --skip-existing Skip files that already exist

Logging:
  --log-level     DEBUG, INFO, WARNING, ERROR
  --log-file      Path to log file
```

## Pipeline Phases

### Phase A: IP Infrastructure (run once per IP)
- **A.1**: Environment (`<ip>_env.sv`)
- **A.2**: Virtual Sequencer (`<ip>_virtual_sequencer.sv`)
- **A.3**: Interface (`<ip>_if.sv`)
- **A.4**: Scoreboard (`<ip>_scoreboard.sv`)

### Phase B: Test Cases (per test in vplan)
- **B.1**: Test file (`TC_xxx_test.sv`)
- **B.2**: Virtual sequence (`TC_xxx_vseq.sv`)

### Phase C: Integration
- **C.1**: Package file (`<ip>_pkg.sv`)

## Output Structure

```
output/
├── ip_infra/
│   ├── env/
│   │   └── my_ip_top_env.sv
│   ├── virtual_sequencer/
│   │   └── my_ip_top_virtual_sequencer.sv
│   ├── interface/
│   │   └── my_ip_top_if.sv
│   ├── scoreboard/
│   │   └── my_ip_top_scoreboard.sv
│   └── pkg/
│       └── my_ip_top_pkg.sv
└── tests/
    ├── tests/
    │   └── TC_BASIC_001_test.sv
    └── virtual_sequences/
        └── TC_BASIC_001_vseq.sv
```

## Configuration Files

### `config/settings.yaml`
Global settings for LLM, output, naming conventions.

### `config/uvc_mapping.yaml` (or custom)
Maps interface names to UVC types, sequences, and sequencers.

## Supported Block YAML Formats

### Standard YAML (recommended)
```yaml
DUT:
  module_name: my_dut
  clock: clk
  reset: resetn
  interfaces:
    m_input_env:
      type: istream_env
      parameters: [64]
```

### Legacy Format (backward compatible)
```
Block:
  Name : my_dut

Clocks:
  name : clk

Interfaces:
  Name : m_input_env
  Kind : istream_env
  params : { DATA_WIDTH : 64 }
```

## Example Files for Few-Shot Learning

For best results, provide example files that match your coding style:

```
examples/
├── env/
│   └── example_env.sv
├── virtual_sequencer/
│   └── example_virtual_sequencer.sv
├── interface/
│   └── example_if.sv
├── Test_case_File/
│   ├── example_test.sv
│   └── example_vseq.sv
└── scoreboard/
    └── example_scoreboard.sv
```

## Troubleshooting

### "API key required" error
Set environment variable or use `--api-key` flag.

### "No UVC mapping found"
Create a UVC mapping file using the template or provide via `--uvc-mapping`.

### Generated code has wrong sequencer names
Ensure your UVC mapping has correct `sequencer_name` entries.

### Parser errors
Check your YAML syntax. The parser supports both standard YAML and legacy formats.

## Extending for New IPs

1. **Create Block YAML**: Describe your DUT, clock, reset, interfaces
2. **Create Vplan YAML**: Define test cases with parameters
3. **Customize UVC Mapping**: Map your interfaces to UVC sequences
4. **Provide Examples**: Better examples = better generated code
5. **Run Generator**: Use appropriate command line options

## License

Internal use only.
