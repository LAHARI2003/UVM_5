@echo off
REM UVM Generator - Example Run Script for Windows
REM ================================================

echo ================================================
echo UVM Generator - LLM-Powered Code Generation
echo ================================================

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY environment variable not set
    echo Please set it: set ANTHROPIC_API_KEY=your-api-key
    exit /b 1
)

REM Run the generator
python generate_uvm.py ^
    --block "../model_files/Block_YAML_file.txt" ^
    --vplan "../model_files/sc_2_gpt_5_2.yaml" ^
    --output "./output" ^
    --examples "../OTHER REQUIRED FILES" ^
    --uvc-lib "../uvc" ^
    --provider anthropic

echo.
echo ================================================
echo Generation complete! Check ./output directory
echo ================================================
pause
