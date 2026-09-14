from pathlib import Path

import pandas as pd


def load_dataset(
    file_path: str,
    protected_columns: dict | None = None,
) -> pd.DataFrame:

    path = Path(file_path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    if protected_columns:
        columns_to_remove = [
            column
            for column in protected_columns
            if column in df.columns
        ]

        if columns_to_remove:
            df = df.drop(columns=columns_to_remove)

    return df


def profile_dataset(
    file_path: str,
    protected_columns: dict | None = None,
) -> dict:

    """
    Generate deterministic statistical metadata
    for non-protected columns only.
    """

    df = load_dataset(
        file_path,
        protected_columns,
    )

    columns = {}

    for column in df.columns:
        series = df[column]

        column_info = {
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": round(
                float(series.isna().mean() * 100),
                2,
            ),
            "unique_count": int(
                series.nunique(dropna=True)
            ),
        }

        if pd.api.types.is_numeric_dtype(series):
            clean_series = series.dropna()

            if not clean_series.empty:
                column_info["statistics"] = {
                    "min": float(clean_series.min()),
                    "max": float(clean_series.max()),
                    "mean": round(
                        float(clean_series.mean()),
                        4,
                    ),
                    "median": float(
                        clean_series.median()
                    ),
                    "std": round(
                        float(clean_series.std()),
                        4,
                    ),
                }

        elif pd.api.types.is_object_dtype(series):
            top_values = (
                series
                .value_counts(dropna=True)
                .head(10)
                .to_dict()
            )

            column_info["top_values"] = {
                str(key): int(value)
                for key, value in top_values.items()
            }

        columns[str(column)] = column_info

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [
            str(column)
            for column in df.columns
        ],
        "columns_profile": columns,
    }