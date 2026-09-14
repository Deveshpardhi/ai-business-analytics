import re
from pathlib import Path

import pandas as pd


PII_PATTERNS = {
    "email": [
        r"email",
        r"e_mail",
        r"email_address",
    ],
    "phone": [
        r"phone",
        r"mobile",
        r"telephone",
        r"contact_number",
    ],
    "address": [
        r"address",
        r"street",
        r"postal_address",
    ],
    "name": [
        r"full_name",
        r"first_name",
        r"last_name",
        r"customer_name",
        r"employee_name",
    ],
    "government_id": [
        r"aadhaar",
        r"pan",
        r"passport",
        r"ssn",
        r"social_security",
        r"driving_license",
    ],
    "financial": [
        r"credit_card",
        r"card_number",
        r"bank_account",
        r"account_number",
    ],
}


PII_VALUE_PATTERNS = {
    "email": re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    ),
    "phone": re.compile(
        r"^(?:\+91[\s-]?)?[6-9]\d{9}$"
    ),
    "aadhaar": re.compile(
        r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}$"
    ),
    "pan": re.compile(
        r"^[A-Z]{5}\d{4}[A-Z]$"
    ),
    "credit_card": re.compile(
        r"^\d{13,19}$"
    ),
}


def detect_pii_columns(df: pd.DataFrame) -> dict:
    """
    Detect potentially sensitive columns using column-name patterns.

    This is deterministic and does not use an LLM.
    """

    detected = {}

    for column in df.columns:
        normalized = str(column).strip().lower()

        for category, patterns in PII_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized):
                    detected[str(column)] = category
                    break

            if str(column) in detected:
                break

    return detected


def detect_pii_values(df: pd.DataFrame) -> dict:
    """
    Detect potentially sensitive columns using cell-value patterns.

    A column is classified as PII when a sufficient proportion
    of its non-empty values match the same PII pattern.
    """

    detected = {}

    for column in df.columns:
        values = df[column].dropna().astype(str).str.strip()

        if values.empty:
            continue

        for category, pattern in PII_VALUE_PATTERNS.items():
            matches = values.apply(
                lambda value: bool(pattern.fullmatch(value))
            )

            match_ratio = matches.mean()

            if match_ratio >= 0.8:
                detected[str(column)] = category
                break

    return detected


def analyze_pii(file_path: str) -> dict:
    """
    Load the dataset and identify potentially sensitive columns
    using both column names and cell values.
    """

    path = Path(file_path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    else:
        raise ValueError("Unsupported file type.")

    name_based_detection = detect_pii_columns(df)
    value_based_detection = detect_pii_values(df)

    detected_columns = {
        **value_based_detection,
        **name_based_detection,
    }

    protected_columns = list(detected_columns.keys())

    safe_columns = [
        column
        for column in df.columns
        if str(column) not in protected_columns
    ]

    return {
        "pii_detected": len(protected_columns) > 0,
        "protected_columns": detected_columns,
        "safe_columns": [str(column) for column in safe_columns],
        "detection_methods": {
            "column_name": name_based_detection,
            "cell_value": value_based_detection,
        },
    }