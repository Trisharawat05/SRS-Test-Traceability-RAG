from pathlib import Path
from pypdf import PdfReader


def extract_pdf(file_path: str) -> dict:
    """
    Extract text and structured page content from a PDF.
    Returns:
        dict: {"text": str, "pages": [{"page_number": int, "text": str}]}
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    reader = PdfReader(path)
    pages_data = []
    text_parts = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages_data.append({
            "page_number": page_number,
            "text": text
        })
        if text:
            text_parts.append(
                f"\n--- PAGE {page_number} ---\n{text}"
            )

    return {
        "text": "\n".join(text_parts),
        "pages": pages_data
    }


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a text-based PDF.
    """
    return extract_pdf(file_path)["text"]