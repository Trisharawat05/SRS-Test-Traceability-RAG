from pathlib import Path


def extract_text_file(file_path: str) -> str:
    """
    Extract text from a plain text or markdown file.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
