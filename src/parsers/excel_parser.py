import pandas as pd
from pathlib import Path


def extract_excel(file_path: str, sheet_name=None):
    """
    Extract data from Excel.
    If sheet_name is None, it extracts all sheets as a dictionary of DataFrames.
    Otherwise, extracts a single sheet as a DataFrame.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df_or_dict = pd.read_excel(
        path,
        sheet_name=sheet_name
    )

    if isinstance(df_or_dict, dict):
        for name in df_or_dict:
            df_or_dict[name] = df_or_dict[name].fillna("")
    else:
        df_or_dict = df_or_dict.fillna("")

    return df_or_dict