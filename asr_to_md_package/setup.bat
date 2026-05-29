@echo off
chcp 65001 >nul
setlocal

set "PROJECT_DIR=%~dp0"
set "BASE_PYTHON=python"
set "ASR_MD_VENV=%USERPROFILE%\.asr-md-venv"
set "ASR_MD_PYTHON=%ASR_MD_VENV%\Scripts\python.exe"
set "PACKAGED_MODEL_DIR=%PROJECT_DIR%models\Qwen3-ASR-0.6B"
set "ASR_MD_MODEL_ROOT=%USERPROFILE%\.asr-md-models"

cd /d "%PROJECT_DIR%"

echo ========================================
echo 语音转 md 本地工具安装
echo ========================================
echo 虚拟环境: %ASR_MD_VENV%
echo 包内模型: %PACKAGED_MODEL_DIR%
echo 用户模型缓存: %ASR_MD_MODEL_ROOT%
echo.

if not exist "%ASR_MD_PYTHON%" (
    echo 创建虚拟环境...
    "%BASE_PYTHON%" -m venv "%ASR_MD_VENV%"
    if errorlevel 1 (
        echo 虚拟环境创建失败，请确认已安装 Python 3.10 或更高版本。
        pause
        exit /b 1
    )
)

echo 升级 pip...
"%ASR_MD_PYTHON%" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

echo 安装运行依赖...
"%ASR_MD_PYTHON%" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn --timeout 120 --retries 3
if errorlevel 1 (
    echo 依赖安装失败，请检查网络或 pip 配置。
    pause
    exit /b 1
)

if exist "%PACKAGED_MODEL_DIR%\model.safetensors" (
    echo 检测到包内 0.6B 模型，跳过模型下载。
) else (
    echo 未检测到包内模型，开始下载 Qwen3-ASR-0.6B 到用户模型缓存...
    "%ASR_MD_PYTHON%" download_models.py --model-root "%ASR_MD_MODEL_ROOT%" --primary Qwen/Qwen3-ASR-0.6B --fallback Qwen/Qwen3-ASR-0.6B
    if errorlevel 1 (
        echo 模型下载失败，请检查网络或 ModelScope 访问。
        pause
        exit /b 1
    )
)

echo.
echo 安装完成。
echo 启动 Web 工具请运行 run_web.bat
echo 命令行转写请运行 transcribe_file.bat 音频文件路径
pause
