from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load a CSV or Excel dataset into a pandas DataFrame.
    """

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if extension == ".csv":
        return pd.read_csv(path)

    return pd.read_excel(path)


def validate_dataset(file_path: str) -> dict:
    """
    Perform deterministic structural validation.
    """

    df = load_dataset(file_path)

    errors = []
    warnings = []

    # Empty dataset
    if df.empty:
        errors.append("Dataset contains no rows.")

    # No columns
    if len(df.columns) == 0:
        errors.append("Dataset contains no columns.")

    # Duplicate column names
    duplicate_columns = df.columns[
        df.columns.duplicated()
    ].tolist()

    if duplicate_columns:
        errors.append(
            f"Duplicate column names found: {duplicate_columns}"
        )

    # Missing values
    missing_values = df.isnull().sum()

    missing_columns = {
        column: int(count)
        for column, count in missing_values.items()
        if count > 0
    }

    if missing_columns:
        warnings.append(
            "Missing values detected."
        )

    # Duplicate rows
    duplicate_rows = int(df.duplicated().sum())

    if duplicate_rows > 0:
        warnings.append(
            f"{duplicate_rows} duplicate rows detected."
        )

    # Basic statistics
    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "missing_values": missing_columns,
        "duplicate_rows": duplicate_rows,
    }

    return result
