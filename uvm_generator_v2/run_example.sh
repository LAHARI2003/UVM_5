#!/bin/bash
# UVM Generator V2 - Example Run Script (Linux/Mac)
# ================================================

# Set your API key here or as environment variable
# export ANTHROPIC_API_KEY=your-api-key-here

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable"
    echo "Example: export ANTHROPIC_API_KEY=your-api-key"
    exit 1
fi

echo "============================================================"
echo "UVM Generator V2 - Running Example"
echo "============================================================"

# Example 1: Full pipeline with custom UVC mapping
# python3 generate_uvm.py \
#     --block examples/block_template.yaml \
#     --vplan examples/vplan_template.yaml \
#     --output output \
#     --uvc-mapping config/uvc_mapping.yaml \
#     --examples ../OTHER\ REQUIRED\ FILES

# Example 2: Using the original DIMC files (backward compatible)
python3 generate_uvm.py \
    --block "../model_files/Block_YAML_file.txt" \
    --vplan "../model_files/sc_2_gpt_5_2.yaml" \
    --output output \
    --examples "../OTHER REQUIRED FILES" \
    --uvc-lib "../uvc" \
    --log-level INFO

echo ""
echo "============================================================"
echo "Generation complete! Check the output directory."
echo "============================================================"
