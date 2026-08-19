from pathlib import Path


SUPPORTED_FORMATS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".xlsx": "excel",
    ".xls": "excel",
    ".csv": "csv",
    ".txt": "text",
    ".md": "text",
}


def detect_format(file_path: str) -> str:

    extension = Path(file_path).suffix.lower()

    if extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return SUPPORTED_FORMATS[extension]