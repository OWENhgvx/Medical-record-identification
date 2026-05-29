# 语音转 md 本地工具

这是从 HIS 病历生成项目中单独拆出的“语音文件转 md 文本”工具。它负责把本地问诊音频识别成 Markdown 转写文本，并按启发式规则初步拆分“医生/患者”角色，便于后续接入病历生成流程。

## 功能

- 支持上传或指定本地 `wav/mp3/m4a/webm/flac` 音频文件。
- 使用本地 Qwen3-ASR 识别中文语音，默认模型为 `Qwen/Qwen3-ASR-0.6B`。
- 自动把 m4a/aac 等音频转成 16kHz 单声道后识别。
- 输出 Markdown 文本和结构化片段，片段包含角色、文本、起止时间和置信度。
- 角色拆分目前是规则启发式，适合测试和草稿流转；正式场景后续可替换为说话人分离模型。

## 目录内容

- `setup.bat`：首次安装运行依赖，并在没有本地模型时下载 0.6B 模型。
- `run_web.bat`：启动本地 Web 上传页面。
- `transcribe_file.bat`：命令行转写单个音频文件。
- `asr_md/`：独立 Python 代码。
- `frontend/`：中文 Web 页面。
- `download_models.py`：从 ModelScope 下载模型。
- `samples/`：测试用合成问诊音频和参考文本。

## 模型说明

GitHub 代码仓库不提交 `models/` 目录和 `.safetensors` 大模型文件，因为单个模型文件超过 GitHub 普通仓库限制。

运行 `setup.bat` 时：

- 如果当前目录已有 `models\Qwen3-ASR-0.6B\model.safetensors`，直接使用包内模型。
- 如果没有包内模型，会自动下载 `Qwen/Qwen3-ASR-0.6B` 到 `%USERPROFILE%\.asr-md-models\Qwen3-ASR-0.6B`。

完整离线压缩包可以单独包含 0.6B 模型，但不要直接提交到 GitHub 普通仓库。

## 首次安装

双击运行：

```bat
setup.bat
```

默认会创建虚拟环境：

```text
%USERPROFILE%\.asr-md-venv
```

## Web 运行

双击运行：

```bat
run_web.bat
```

浏览器访问：

```text
http://127.0.0.1:8010
```

上传音频文件后，会输出可复制到病历生成系统的 md 文本。

## 命令行运行

```bat
transcribe_file.bat samples\medical_consultation_sample.wav
```

默认会在音频同目录生成同名 `.md` 文件。也可以指定输出路径：

```bat
transcribe_file.bat samples\medical_consultation_sample.wav output.md
```

## 运行配置

可在运行前设置环境变量：

```bat
set ASR_MD_MODEL=Qwen/Qwen3-ASR-1.7B
set ASR_MD_FALLBACK_MODEL=Qwen/Qwen3-ASR-0.6B
set ASR_MD_DEVICE=cpu
set ASR_MD_MODEL_DIR=D:\models\Qwen3-ASR-1.7B
set ASR_MD_FALLBACK_MODEL_DIR=%USERPROFILE%\.asr-md-models\Qwen3-ASR-0.6B
set ASR_MD_FALLBACK_THRESHOLD_SECONDS=180
```

当前 Windows AMD 显卡环境默认走 CPU。没有 NVIDIA CUDA 时，不建议把 `ASR_MD_DEVICE` 改成 `cuda`。

## 输出 md 示例

```md
# 语音识别转写

- 医生：您好，哪里不舒服？
- 患者：我咳嗽三天了，还有点发烧。

## 识别信息

- 模型：Qwen/Qwen3-ASR-0.6B
- 是否使用兜底模型：否
- 音频时长：79.56 秒
- 识别耗时：38.50 秒
```

## 注意事项

- 本工具只生成转写草稿，不直接写入正式 HIS 病历。
- 医生/患者角色拆分为规则推断，必须允许人工修正。
- CPU 首次识别会加载模型，耗时较长；同一 Web 服务进程内后续请求会复用已加载模型。
