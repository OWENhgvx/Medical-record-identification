from __future__ import annotations

import argparse
import json
from pathlib import Path

from asr_md.core import AsrToMarkdownConverter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a local audio file to Markdown transcript.")
    parser.add_argument("audio", help="Path to wav/mp3/m4a/webm/flac audio file.")
    parser.add_argument("-o", "--output", help="Markdown output path. Defaults to audio filename with .md.")
    parser.add_argument("--json", action="store_true", help="Print full JSON result instead of Markdown.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    audio_path = Path(args.audio).resolve()
    if not audio_path.exists():
        raise SystemExit(f"音频文件不存在：{audio_path}")

    result = AsrToMarkdownConverter().transcribe_to_markdown(audio_path)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    output_path = Path(args.output).resolve() if args.output else audio_path.with_suffix(".md")
    output_path.write_text(result["markdown"], encoding="utf-8")
    print(f"已生成：{output_path}")
    print(f"模型：{result['model_name']}")
    print(f"耗时：{result['elapsed_seconds']:.2f} 秒")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
