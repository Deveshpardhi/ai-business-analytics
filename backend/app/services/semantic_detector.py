import re
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Column-name patterns
# ---------------------------------------------------------

ID_PATTERNS = [
    r"(^|_)id$",
    r"(^|_)id(_|$)",
    r"^[a-z]+id$",
    r"(^|_)code$",
    r"uuid",
    r"identifier",
]

DATE_PATTERNS = [
    r"date",
    r"time",
    r"timestamp",
    r"month",
    r"year",
]

MEASURE_PATTERNS = [
    r"sales",
    r"revenue",
    r"amount",
    r"price",
    r"cost",
    r"profit",
    r"quantity",
    r"units",
    r"discount",
    r"margin",
    r"salary",
    r"wage",
    r"compensation",
]

DIMENSION_PATTERNS = [
    r"region",
    r"country",
    r"state",
    r"city",
    r"category",
    r"product",
    r"department",
    r"segment",
    r"type",
    r"status",
]


# ---------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------

def matches_pattern(
    column_name: str,
    patterns: list[str],
) -> bool:
    """
    Check whether a column name matches any pattern.
    """

    normalized = column_name.strip().lower()

    return any(
        re.search(pattern, normalized)
        for pattern in patterns
    )


# ---------------------------------------------------------
# Role detection
# ---------------------------------------------------------

def detect_column_role(
    column_name: str,
    series: pd.Series,
) -> str:
    """
    Determine the semantic role of a column.

    Priority:
    1. Identifier
    2. Date
    3. Numeric measure
    4. Other numeric
    5. Known dimension
    6. Low-cardinality text dimension
    7. Unknown
    """

    # -----------------------------------------------------
    # 1. Identifier
    # -----------------------------------------------------

    if matches_pattern(
        column_name,
        ID_PATTERNS,
    ):
        return "identifier"

    # -----------------------------------------------------
    # 2. Date
    # -----------------------------------------------------

    if matches_pattern(
        column_name,
        DATE_PATTERNS,
    ):
        return "date"

    # -----------------------------------------------------
    # 3. Numeric columns
    # -----------------------------------------------------

    if pd.api.types.is_numeric_dtype(series):

        # Known business measure
        if matches_pattern(
            column_name,
            MEASURE_PATTERNS,
        ):
            return "measure"

        # Numeric column without known business meaning
        return "numeric"

    # -----------------------------------------------------
    # 4. Known dimensions
    # -----------------------------------------------------

    if matches_pattern(
        column_name,
        DIMENSION_PATTERNS,
    ):
        return "dimension"

    # -----------------------------------------------------
    # 5. Low-cardinality text
    # -----------------------------------------------------

    if pd.api.types.is_string_dtype(series):

        unique_count = series.nunique(
            dropna=True
        )

        if unique_count <= 50:
            return "dimension"

    # -----------------------------------------------------
    # 6. Unknown
    # -----------------------------------------------------

    return "unknown"


# ---------------------------------------------------------
# Main semantic inference
# ---------------------------------------------------------

def infer_semantics(
    file_path: str,
    protected_columns: dict | None = None,
) -> dict:
    """
    Infer semantic roles for every dataset column.
    """

    path = Path(file_path)

    # -----------------------------------------------------
    # Load dataset
    # -----------------------------------------------------

    if path.suffix.lower() == ".csv":

        df = pd.read_csv(path)

    elif path.suffix.lower() in {".xlsx", ".xls"}:

        df = pd.read_excel(path)

    else:

        raise ValueError(
            f"Unsupported file type: {path.suffix}"
        )

    # -----------------------------------------------------
    # Remove protected columns
    # -----------------------------------------------------

    if protected_columns:

        columns_to_remove = [
            column
            for column in protected_columns
            if column in df.columns
        ]

        if columns_to_remove:
            df = df.drop(
                columns=columns_to_remove
            )

    # -----------------------------------------------------
    # Analyze columns
    # -----------------------------------------------------

    columns = {}

    for column in df.columns:

        column_name = str(column)

        role = detect_column_role(
            column_name,
            df[column],
        )

        columns[column_name] = {
            "role": role,
            "dtype": str(
                df[column].dtype
            ),
            "unique_count": int(
                df[column].nunique(
                    dropna=True
                )
            ),
            "null_count": int(
                df[column].isna().sum()
            ),
        }

    # -----------------------------------------------------
    # Return semantic metadata
    # -----------------------------------------------------

    return {
        "columns": columns,
    }