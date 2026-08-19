from pathlib import Path

from ingestion.document import DocumentContent

from parsers.pdf_parser import extract_pdf
from parsers.docx_parser import extract_docx
from parsers.excel_parser import extract_excel
from parsers.csv_parser import extract_csv
from parsers.text_parser import extract_text_file


def load_document(file_path: str) -> DocumentContent:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    extension = path.suffix.lower()

    # PDF
    if extension == ".pdf":
        pdf_data = extract_pdf(file_path)
        return DocumentContent(
            file_name=path.name,
            file_type="pdf",
            text=pdf_data["text"],
            pages=pdf_data["pages"],
            tables=[],
            metadata={}
        )

    # DOCX
    elif extension == ".docx":
        docx_data = extract_docx(file_path)
        return DocumentContent(
            file_name=path.name,
            file_type="docx",
            text=docx_data["text"],
            pages=[],
            tables=docx_data["tables"],
            metadata={}
        )

    # Excel
    elif extension in [".xlsx", ".xls"]:
        df_or_dict = extract_excel(file_path)
        
        tables = []
        text_parts = []
        
        if isinstance(df_or_dict, dict):
            # Multiple sheets
            for sheet_name, df in df_or_dict.items():
                text_parts.append(f"--- Sheet: {sheet_name} ---")
                text_parts.append(df.to_string(index=False))
                tables.append({
                    "name": sheet_name,
                    "columns": df.columns.tolist(),
                    "rows": df.values.tolist()
                })
        else:
            # Single sheet
            text_parts.append(df_or_dict.to_string(index=False))
            tables.append({
                "name": "Sheet1",
                "columns": df_or_dict.columns.tolist(),
                "rows": df_or_dict.values.tolist()
            })
            
        return DocumentContent(
            file_name=path.name,
            file_type="excel",
            text="\n".join(text_parts),
            pages=[],
            tables=tables,
            metadata={}
        )

    # CSV
    elif extension == ".csv":
        dataframe = extract_csv(file_path)
        return DocumentContent(
            file_name=path.name,
            file_type="csv",
            text=dataframe.to_string(index=False),
            pages=[],
            tables=[
                {
                    "name": "csv",
                    "columns": dataframe.columns.tolist(),
                    "rows": dataframe.values.tolist()
                }
            ],
            metadata={}
        )

    # Plain Text / Markdown
    elif extension in [".txt", ".md"]:
        text = extract_text_file(file_path)
        return DocumentContent(
            file_name=path.name,
            file_type="text",
            text=text,
            pages=[],
            tables=[],
            metadata={}
        )

    else:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )