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

if not exist "%ASR_MD_PYTHON%" (
    echo 未找到虚拟环境，请先运行 setup.bat
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

echo ========================================
echo 语音转 md 本地工具
echo ========================================
echo 地址: http://127.0.0.1:8010
echo 主模型: %ASR_MD_MODEL%
echo 兜底模型: %ASR_MD_FALLBACK_MODEL%
echo 包内模型目录: %ASR_MD_MODEL_DIR%
echo.

start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8010/"
"%ASR_MD_PYTHON%" -m uvicorn asr_md.api:app --host 127.0.0.1 --port 8010

echo.
echo 服务已停止。
pause
