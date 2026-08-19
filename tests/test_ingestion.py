from src.parsers.file_detector import detect_format


def test_pdf_detection():

    assert detect_format("example.pdf") == "pdf"


def test_excel_detection():

    assert detect_format("example.xlsx") == "excel"


def test_docx_detection():

    assert detect_format("example.docx") == "docx"


def test_csv_detection():

    assert detect_format("example.csv") == "csv"