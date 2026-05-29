from __future__ import annotations

import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

PACKAGE_DIR = Path(__file__).resolve().parent.parent
PACKAGED_0_6B_DIR = PACKAGE_DIR / "models" / "Qwen3-ASR-0.6B"


@dataclass
class AsrMdConfig:
    model_name: str
    fallback_model_name: str
    model_dir: Path
    fallback_model_dir: Path
    device: str
    language: str
    fallback_threshold_seconds: float
    max_new_tokens: int

    @classmethod
    def from_env(cls) -> "AsrMdConfig":
        model_root = Path(os.getenv("ASR_MD_MODEL_ROOT", Path.home() / ".asr-md-models"))
        default_0_6b_dir = PACKAGED_0_6B_DIR if PACKAGED_0_6B_DIR.exists() else model_root / "Qwen3-ASR-0.6B"
        return cls(
            model_name=os.getenv("ASR_MD_MODEL", "Qwen/Qwen3-ASR-0.6B"),
            fallback_model_name=os.getenv("ASR_MD_FALLBACK_MODEL", "Qwen/Qwen3-ASR-0.6B"),
            model_dir=Path(os.getenv("ASR_MD_MODEL_DIR", default_0_6b_dir)),
            fallback_model_dir=Path(os.getenv("ASR_MD_FALLBACK_MODEL_DIR", default_0_6b_dir)),
            device=os.getenv("ASR_MD_DEVICE", "cpu"),
            language=os.getenv("ASR_MD_LANGUAGE", "zh"),
            fallback_threshold_seconds=float(os.getenv("ASR_MD_FALLBACK_THRESHOLD_SECONDS", "180")),
            max_new_tokens=int(os.getenv("ASR_MD_MAX_NEW_TOKENS", "512")),
        )


class AsrToMarkdownConverter:
    def __init__(self, config: Optional[AsrMdConfig] = None):
        self.config = config or AsrMdConfig.from_env()
        self._models: Dict[str, Any] = {}

    def health(self) -> Dict[str, Any]:
        return {
            "model_name": self.config.model_name,
            "fallback_model_name": self.config.fallback_model_name,
            "device": self.config.device,
            "language": self.config.language,
            "model_dir": str(self.config.model_dir),
            "fallback_model_dir": str(self.config.fallback_model_dir),
            "model_exists": self.config.model_dir.exists(),
            "fallback_model_exists": self.config.fallback_model_dir.exists(),
        }

    def transcribe_to_markdown(self, audio_path: Path) -> Dict[str, Any]:
        try:
            result = self._transcribe_with_model(
                self._checkpoint(self.config.model_name, self.config.model_dir),
                self.config.model_name,
                audio_path,
            )
            if (
                self.config.fallback_model_name != self.config.model_name
                and result["transcribe_seconds"] > self.config.fallback_threshold_seconds
            ):
                fallback = self._transcribe_with_fallback(audio_path)
                fallback["fallback_reason"] = (
                    f"主模型转写耗时 {result['transcribe_seconds']:.2f} 秒，"
                    f"超过阈值 {self.config.fallback_threshold_seconds:.2f} 秒。"
                )
                result = fallback
            else:
                result["used_fallback"] = False
                result["fallback_reason"] = None
        except Exception as primary_exc:
            if self.config.fallback_model_name == self.config.model_name:
                raise
            result = self._transcribe_with_fallback(audio_path)
            result["fallback_reason"] = f"主模型加载或转写失败，已降级兜底模型：{primary_exc}"

        result["markdown"] = result_to_markdown(result)
        return result

    def _transcribe_with_fallback(self, audio_path: Path) -> Dict[str, Any]:
        result = self._transcribe_with_model(
            self._checkpoint(self.config.fallback_model_name, self.config.fallback_model_dir),
            self.config.fallback_model_name,
            audio_path,
        )
        result["used_fallback"] = True
        return result

    def _transcribe_with_model(self, checkpoint: str, model_name: str, audio_path: Path) -> Dict[str, Any]:
        prepared_audio, cleanup_audio = prepare_audio(audio_path)
        try:
            load_started = time.perf_counter()
            model = self._load_model(checkpoint, model_name)
            load_seconds = time.perf_counter() - load_started

            transcribe_started = time.perf_counter()
            results = model.transcribe(
                audio=str(prepared_audio),
                language=language_name(self.config.language),
                return_time_stamps=False,
            )
            transcribe_seconds = time.perf_counter() - transcribe_started
            first = results[0]
            text = getattr(first, "text", "") or ""
            detected_language = getattr(first, "language", None)
            duration = audio_duration_seconds(prepared_audio)
            segments = split_dialogue_segments(text, duration) if text else []
            return {
                "model_name": model_name,
                "used_fallback": False,
                "fallback_reason": None,
                "language": detected_language,
                "duration_seconds": duration,
                "load_seconds": load_seconds,
                "transcribe_seconds": transcribe_seconds,
                "elapsed_seconds": load_seconds + transcribe_seconds,
                "text": text,
                "segments": segments,
            }
        finally:
            cleanup_audio()

    def _load_model(self, checkpoint: str, model_name: str) -> Any:
        if model_name in self._models:
            return self._models[model_name]

        import torch
        from qwen_asr import Qwen3ASRModel

        kwargs: Dict[str, Any] = {
            "max_inference_batch_size": 1,
            "max_new_tokens": self.config.max_new_tokens,
        }
        if self.config.device.lower().startswith("cuda"):
            kwargs.update({"dtype": torch.bfloat16, "device_map": self.config.device})
        else:
            kwargs.update({"dtype": torch.float32, "device_map": "cpu"})

        model = Qwen3ASRModel.from_pretrained(checkpoint, **kwargs)
        self._models[model_name] = model
        return model

    @staticmethod
    def _checkpoint(model_name: str, model_dir: Path) -> str:
        return str(model_dir) if model_dir.exists() else model_name


def result_to_markdown(result: Dict[str, Any]) -> str:
    lines: List[str] = ["# 语音识别转写", ""]
    segments = result.get("segments") or []
    if segments:
        for segment in segments:
            text = str(segment.get("text", "")).strip()
            if text:
                role = speaker_role_label(str(segment.get("speaker_role", "unknown")))
                lines.append(f"- {role}：{text}")
    elif str(result.get("text", "")).strip():
        lines.append(f"- 未知：{str(result['text']).strip()}")
    else:
        lines.append("- 未知：")

    lines.extend(
        [
            "",
            "## 识别信息",
            "",
            f"- 模型：{result.get('model_name', '')}",
            f"- 是否使用兜底模型：{'是' if result.get('used_fallback') else '否'}",
            f"- 音频时长：{float(result.get('duration_seconds') or 0):.2f} 秒",
            f"- 识别耗时：{float(result.get('elapsed_seconds') or 0):.2f} 秒",
        ]
    )
    if result.get("fallback_reason"):
        lines.append(f"- 降级原因：{result['fallback_reason']}")
    return "\n".join(lines).strip() + "\n"


def split_dialogue_segments(text: str, duration_seconds: float) -> List[Dict[str, Any]]:
    utterances = split_utterances(text)
    if not utterances:
        return []

    grouped: List[Dict[str, str]] = []
    previous_role = "unknown"
    for index, utterance in enumerate(utterances):
        role = classify_speaker_role(utterance, previous_role, index)
        if grouped and grouped[-1]["speaker_role"] == role:
            grouped[-1]["text"] = f"{grouped[-1]['text']}{utterance}"
        else:
            grouped.append({"speaker_role": role, "text": utterance})
        previous_role = role

    total_chars = max(sum(len(item["text"]) for item in grouped), 1)
    cursor = 0.0
    segments: List[Dict[str, Any]] = []
    for index, item in enumerate(grouped, start=1):
        ratio = len(item["text"]) / total_chars
        span = round(duration_seconds * ratio, 3)
        end_time = duration_seconds if index == len(grouped) else min(duration_seconds, cursor + span)
        segments.append(
            {
                "segment_id": f"asr_{index:04d}",
                "speaker_role": item["speaker_role"],
                "start_time": round(cursor, 3),
                "end_time": round(end_time, 3),
                "text": item["text"],
                "confidence": 0.75,
            }
        )
        cursor = end_time
    return segments


def split_utterances(text: str) -> List[str]:
    normalized = re.sub(r"\s+", "", text or "")
    parts = [part.strip() for part in re.findall(r"[^。！？!?；;]+[。！？!?；;]?", normalized) if part.strip()]
    utterances: List[str] = []
    for part in parts:
        utterances.extend(split_mixed_utterance(part))
    return utterances


def split_mixed_utterance(text: str) -> List[str]:
    boundary_cues = ["最高烧到", "有没有", "以前有", "对什么药", "哪里不舒服", "多久", "建议", "考虑"]
    indexes = [text.find(cue) for cue in boundary_cues if text.find(cue) > 5]
    if not indexes:
        return [text]
    boundary = min(indexes)
    prefix = text[:boundary].rstrip("，,、 ")
    suffix = text[boundary:]
    patientish_prefix = any(cue in prefix for cue in ["我", "咳", "痰", "烧", "疼", "喘", "没有", "有点"])
    if prefix and suffix and patientish_prefix:
        if not prefix.endswith(("。", "！", "？", "!", "?")):
            prefix = f"{prefix}。"
        return [prefix, suffix]
    return [text]


def classify_speaker_role(text: str, previous_role: str, index: int) -> str:
    normalized = text.strip()
    if not normalized:
        return previous_role if previous_role != "unknown" else "patient"

    has_question = normalized.endswith(("？", "?")) or any(cue in normalized for cue in ["吗", "么", "多少", "哪里", "多久"])

    if normalized.startswith(("患者：", "病人：", "家属：")):
        return "patient"
    if normalized.startswith(("医生：", "医师：", "大夫：")) and not re.match(r"^(医生|医师|大夫)[，,]?(我|俺|我们)", normalized):
        return "doctor"
    if "谢谢医生" in normalized or "谢谢大夫" in normalized:
        return "patient"
    if previous_role == "doctor" and not has_question and any(
        cue in normalized for cue in ["最高昨天", "最高今天", "没超过", "没有", "有点", "小时候", "不清楚"]
    ):
        return "patient"

    doctor_score = 0
    patient_score = 0
    doctor_cues = [
        "哪里不舒服",
        "什么问题",
        "多久",
        "几天",
        "多少度",
        "最高",
        "有没有",
        "是否",
        "需要",
        "建议",
        "考虑",
        "先查",
        "检查",
        "血常规",
        "拍片",
        "听一下",
        "复诊",
        "急诊",
        "用药",
        "开药",
        "过敏",
        "既往",
        "病史",
    ]
    patient_cues = [
        "我",
        "俺",
        "我们",
        "就是",
        "感觉",
        "有点",
        "没有",
        "大概",
        "昨天",
        "今天",
        "晚上",
        "早上",
        "不知道",
        "小时候",
        "同事",
        "家里",
        "好的",
        "明白",
    ]
    for cue in doctor_cues:
        if cue in normalized:
            doctor_score += 2
    for cue in patient_cues:
        if cue in normalized:
            patient_score += 1

    if has_question and doctor_score > 0:
        doctor_score += 2
    if has_question and previous_role == "patient" and doctor_score == 0 and len(normalized) <= 10:
        patient_score += 2

    if patient_score > doctor_score:
        return "patient"
    if doctor_score > patient_score:
        return "doctor"
    if has_question:
        return "doctor"
    if previous_role != "unknown":
        return previous_role
    return "doctor" if index == 0 else "patient"


def speaker_role_label(role: str) -> str:
    return {"doctor": "医生", "patient": "患者", "family": "家属"}.get(role, "未知")


def prepare_audio(audio_path: Path) -> Tuple[Path, Callable[[], None]]:
    try:
        import librosa
        import soundfile as sf

        info = sf.info(str(audio_path))
        if audio_path.suffix.lower() == ".wav" and info.samplerate == 16000 and info.channels == 1:
            return audio_path, lambda: None

        samples, _ = librosa.load(str(audio_path), sr=16000, mono=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = Path(temp_file.name)
        sf.write(str(temp_path), samples, 16000, subtype="PCM_16")
        return temp_path, lambda: temp_path.unlink(missing_ok=True)
    except Exception:
        return prepare_audio_with_av(audio_path)


def prepare_audio_with_av(audio_path: Path) -> Tuple[Path, Callable[[], None]]:
    try:
        import av
        import numpy as np
        import soundfile as sf

        with av.open(str(audio_path)) as container:
            audio_stream = next((stream for stream in container.streams if stream.type == "audio"), None)
            if audio_stream is None:
                return audio_path, lambda: None

            resampler = av.audio.resampler.AudioResampler(format="s16", layout="mono", rate=16000)
            chunks = []
            for frame in container.decode(audio_stream):
                resampled_frames = resampler.resample(frame)
                if not isinstance(resampled_frames, list):
                    resampled_frames = [resampled_frames]
                for resampled in resampled_frames:
                    array = resampled.to_ndarray()
                    if array.ndim > 1:
                        array = array.reshape(-1)
                    chunks.append(array.astype("float32") / 32768.0)

        if not chunks:
            return audio_path, lambda: None

        samples = np.concatenate(chunks)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = Path(temp_file.name)
        sf.write(str(temp_path), samples, 16000, subtype="PCM_16")
        return temp_path, lambda: temp_path.unlink(missing_ok=True)
    except Exception:
        return audio_path, lambda: None


def audio_duration_seconds(audio_path: Path) -> float:
    try:
        import soundfile as sf

        info = sf.info(str(audio_path))
        if info.samplerate:
            return round(float(info.frames) / float(info.samplerate), 3)
    except Exception:
        return 0.0
    return 0.0


def language_name(value: str) -> Optional[str]:
    normalized = (value or "").strip().lower()
    if normalized in {"", "auto", "none"}:
        return None
    if normalized in {"zh", "cn", "chinese", "中文", "汉语"}:
        return "Chinese"
    return value
