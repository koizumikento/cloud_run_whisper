import argparse
import logging
import os

from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("download_model")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predownload faster-whisper model weights")
    parser.add_argument(
        "--model",
        default=os.getenv("WHISPER_MODEL", "large-v3-turbo"),
        help="Model name or local path",
    )
    parser.add_argument(
        "--device",
        default=os.getenv("WHISPER_DEVICE", "cpu"),
        choices=["cpu", "cuda"],
        help="Device to initialize on (cpu at build)",
    )
    parser.add_argument(
        "--compute-type",
        default=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        help="Compute type (e.g., int8, int8_float16, float16, float32)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cache_home = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    logger.info("XDG_CACHE_HOME=%s", cache_home)
    logger.info("Downloading model '%s' on %s (%s)", args.model, args.device, args.compute_type)

    # Instantiate to trigger download into cache
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    # Access a property to ensure model is fully materialized
    _ = getattr(model, "model_size", None)
    logger.info("Model predownload complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
