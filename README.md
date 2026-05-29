# Medical-record-identification

医患对话病历识别系统的本地实验仓库。当前已上传第一阶段能力：语音识别转 Markdown 工具。

## 已包含功能

- 本地 Qwen3-ASR 中文语音识别。
- 支持 `wav/mp3/m4a/webm/flac` 音频上传。
- m4a/aac 音频自动转 16kHz 单声道后识别。
- 输出 Markdown 转写文本。
- 按启发式规则初步拆分“医生/患者”角色。
- 提供中文 Web 页面和命令行脚本。

## 快速运行

进入工具目录：

```bat
cd asr_to_md_package
```

首次安装：

```bat
setup.bat
```

启动 Web 页面：

```bat
run_web.bat
```

浏览器访问：

```text
http://127.0.0.1:8010
```

命令行转写：

```bat
transcribe_file.bat samples\medical_consultation_sample.wav
```

## 模型说明

本仓库不提交大模型文件和压缩包。`setup.bat` 会在本地没有模型时自动下载 `Qwen/Qwen3-ASR-0.6B` 到：

```text
%USERPROFILE%\.asr-md-models\Qwen3-ASR-0.6B
```

如需离线运行，可以把模型目录放到：

```text
asr_to_md_package\models\Qwen3-ASR-0.6B
```

## 后续计划

- 将转写结果接入结构化病历生成 Agent。
- 增加人工修正医生/患者角色的前端交互。
- 将启发式角色拆分替换为独立说话人分离能力。
- 增加病历生成字段证据追溯和医生审核流程。
