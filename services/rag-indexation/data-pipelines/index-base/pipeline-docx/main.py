import sys
from pathlib import Path
import argparse

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from pipeline.ingest_and_embed import ingest_file
from config import DEFAULT_INPUT_FILE


def parse_args() -> str:
    parser = argparse.ArgumentParser(
        description="Ingestar y embeber un documento DOCX en pgvector"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=DEFAULT_INPUT_FILE,
        help=f"Ruta al archivo .docx a ingerir (por defecto: {DEFAULT_INPUT_FILE})",
    )
    args = parser.parse_args()
    return args.file


def main() -> None:
    file_path = parse_args()
    ingest_file(file_path)


if __name__ == "__main__":
    main()
