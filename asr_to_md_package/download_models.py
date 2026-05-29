from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Qwen3-ASR models from ModelScope.")
    parser.add_argument("--model-root", default=str(Path.home() / ".asr-md-models"))
    parser.add_argument("--primary", default="Qwen/Qwen3-ASR-1.7B")
    parser.add_argument("--fallback", default="Qwen/Qwen3-ASR-0.6B")
    return parser


def main() -> int:
    from modelscope import snapshot_download

    args = build_parser().parse_args()
    model_root = Path(args.model_root)
    downloads: Dict[str, Path] = {}
    for model_id in [args.primary, args.fallback]:
        model_name = model_id.rstrip("/").split("/")[-1]
        downloads.setdefault(model_id, model_root / model_name)

    results: List[Dict[str, str | bool]] = []
    for model_id, target_dir in downloads.items():
        target_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(model_id, local_dir=str(target_dir))
        results.append({"model": model_id, "target": str(target_dir), "ok": True})

    print(json.dumps({"downloads": results}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
