"""Load local vehicle reference data for development and diagnostics."""

import pandas as pd
from pathlib import Path

def load_vehicle_data(path: str = "data/merge.xlsx"):
    """Load an Excel vehicle-data file and normalize its column names."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not Found {path.resolve()}")

    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    return df