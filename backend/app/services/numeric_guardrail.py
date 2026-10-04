import re
from numbers import Number


ALLOWED_NUMERIC_FIELDS = {
    "evidence",
    "verification",
}


def extract_numbers(value):
    numbers = []

    if isinstance(value, Number) and not isinstance(value, bool):
        numbers.append(float(value))

    elif isinstance(value, str):
        for line in value.splitlines():
            stripped = line.lstrip()

            # Ignore Markdown ordered-list markers such as:
            # "1. First point"
            # "2. Second point"
            if re.match(r"^\d+\.\s", stripped):
                stripped = re.sub(r"^\d+\.\s", "", stripped)

            matches = re.findall(
                r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
                stripped,
            )
            numbers.extend(float(match) for match in matches)

    elif isinstance(value, dict):
        for item in value.values():
            numbers.extend(extract_numbers(item))

    elif isinstance(value, list):
        for item in value:
            numbers.extend(extract_numbers(item))

    return numbers


def numbers_match(value_a, value_b):
    """Require the provider to preserve authoritative values exactly."""
    return value_a == value_b


def extract_allowed_numbers(insight):
    numbers = []

    for field in ALLOWED_NUMERIC_FIELDS:
        if field in insight:
            numbers.extend(
                extract_numbers(insight[field])
            )

    return numbers


def validate_explanation_numbers(explanation, insight):
    explanation_numbers = extract_numbers(explanation)
    allowed_numbers = extract_allowed_numbers(insight)

    unsupported_numbers = []

    for number in explanation_numbers:
        if not any(
            numbers_match(number, allowed)
            for allowed in allowed_numbers
        ):
            unsupported_numbers.append(number)

    return {
        "valid": len(unsupported_numbers) == 0,
        "unsupported_numbers": unsupported_numbers,
    }
