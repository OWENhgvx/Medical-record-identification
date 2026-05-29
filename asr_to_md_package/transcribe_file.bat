@echo off
chcp 65001 >nul
setlocal

set "PROJECT_DIR=%~dp0"
set "ASR_MD_VENV=%USERPROFILE%\.asr-md-venv"
set "ASR_MD_PYTHON=%ASR_MD_VENV%\Scripts\python.exe"
set "ASR_MD_MODEL=Qwen/Qwen3-ASR-0.6B"
set "ASR_MD_FALLBACK_MODEL=Qwen/Qwen3-ASR-0.6B"
set "PACKAGED_MODEL_DIR=%PROJECT_DIR%models\Qwen3-ASR-0.6B"
if exist "%PACKAGED_MODEL_DIR%\model.safetensors" (
    set "ASR_MD_MODEL_DIR=%PACKAGED_MODEL_DIR%"
) else (
    set "ASR_MD_MODEL_DIR=%USERPROFILE%\.asr-md-models\Qwen3-ASR-0.6B"
)
set "ASR_MD_FALLBACK_MODEL_DIR=%ASR_MD_MODEL_DIR%"
set "ASR_MD_DEVICE=cpu"

if "%~1"=="" (
    echo 用法: transcribe_file.bat 音频文件路径 [输出md路径]
    pause
    exit /b 1
)

if not exist "%ASR_MD_PYTHON%" (
    echo 未找到虚拟环境，请先运行 setup.bat
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

if "%~2"=="" (
    "%ASR_MD_PYTHON%" -m asr_md.cli "%~1"
) else (
    "%ASR_MD_PYTHON%" -m asr_md.cli "%~1" --output "%~2"
)

pause
