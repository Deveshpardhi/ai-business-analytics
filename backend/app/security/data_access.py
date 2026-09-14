from pathlib import Path

import pandas as pd


def load_safe_dataset(
    file_path: str,
    protected_columns: dict,
) -> pd.DataFrame:
    path = Path(file_path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Unsupported file type.")

    columns_to_remove = [
        column
        for column in protected_columns
        if column in df.columns
    ]

    if columns_to_remove:
        df = df.drop(columns=columns_to_remove)

    return df
