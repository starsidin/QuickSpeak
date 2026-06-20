"""Download the Qwen3-ASR model for the QuickSpeak backend."""

import argparse
import os
import sys
from pathlib import Path


MODEL_ID = "Qwen/Qwen3-ASR-1.7B"
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models" / "Qwen3-ASR-1.7B"


def model_is_ready() -> bool:
    """Use model metadata and at least one weight file as a completeness guard."""
    return (
        (MODEL_DIR / "config.json").is_file()
        and any(MODEL_DIR.glob("*.safetensors"))
    )


def choose_source() -> str:
    print("\nQuickSpeak 后端首次启动需要下载 Qwen3-ASR-1.7B 模型（约 3.4 GB）。")
    print("  1. ModelScope（推荐，中国大陆网络优先）")
    print("  2. Hugging Face（国际网络）")
    while True:
        choice = input("请选择下载源 [1/2，默认 1]: ").strip() or "1"
        if choice == "1":
            return "modelscope"
        if choice == "2":
            return "huggingface"
        print("输入无效，请输入 1 或 2。")


def download_from_modelscope() -> str:
    from modelscope import snapshot_download

    return snapshot_download(MODEL_ID, local_dir=str(MODEL_DIR))


def download_from_huggingface() -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(repo_id=MODEL_ID, local_dir=str(MODEL_DIR))


def main() -> int:
    parser = argparse.ArgumentParser(description="下载 QuickSpeak 后端 Qwen3-ASR 模型")
    parser.add_argument(
        "--source",
        choices=("modelscope", "huggingface"),
        help="跳过交互，直接指定下载源",
    )
    parser.add_argument("--force", action="store_true", help="即使模型已存在也重新下载")
    args = parser.parse_args()

    if model_is_ready() and not args.force:
        print(f"模型已存在：{MODEL_DIR}")
        return 0

    source = args.source or choose_source()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    source_name = "ModelScope" if source == "modelscope" else "Hugging Face"
    print(f"\n正在通过 {source_name} 下载 {MODEL_ID}")
    print(f"保存目录：{MODEL_DIR}")

    try:
        if source == "modelscope":
            result = download_from_modelscope()
        else:
            result = download_from_huggingface()
    except KeyboardInterrupt:
        print("\n下载已取消。")
        return 130
    except Exception as exc:
        print(f"\n下载失败：{exc}")
        print("可重新运行本脚本，并尝试另一个下载源。")
        return 1

    if not model_is_ready():
        print("下载结束，但模型文件不完整，请重新下载。")
        return 1

    print(f"\n模型下载完成：{result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
