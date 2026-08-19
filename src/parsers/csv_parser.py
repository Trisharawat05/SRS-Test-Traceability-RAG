import pandas as pd
from pathlib import Path


def extract_csv(file_path: str):

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(path).fillna("")