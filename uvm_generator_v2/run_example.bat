@echo off
REM UVM Generator V2 - Example Run Script (Windows)
REM ================================================

REM Set your API key here or as environment variable
REM set ANTHROPIC_API_KEY=your-api-key-here

REM Check if API key is set
if "%ANTHROPIC_API_KEY%"=="" (
    if "%OPENAI_API_KEY%"=="" (
        echo ERROR: Please set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable
        echo Example: set ANTHROPIC_API_KEY=your-api-key
        exit /b 1
    )
)

echo ============================================================
echo UVM Generator V2 - Running Example
echo ============================================================

REM Example 1: Full pipeline with custom UVC mapping
REM python generate_uvm.py ^
REM     --block examples\block_template.yaml ^
REM     --vplan examples\vplan_template.yaml ^
REM     --output output ^
REM     --uvc-mapping config\uvc_mapping.yaml ^
REM     --examples ..\OTHER REQUIRED FILES

REM Example 2: Using the original DIMC files (backward compatible)
python generate_uvm.py ^
    --block "..\model_files\Block_YAML_file.txt" ^
    --vplan "..\model_files\sc_2_gpt_5_2.yaml" ^
    --output output ^
    --examples "..\OTHER REQUIRED FILES" ^
    --uvc-lib "..\uvc" ^
    --log-level INFO

echo.
echo ============================================================
echo Generation complete! Check the output directory.
echo ============================================================
pause
