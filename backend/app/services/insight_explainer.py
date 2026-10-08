import math
from copy import deepcopy

import logging
import os

from pydantic import ValidationError

from app.schemas.explanation import (
    ExplanationResponse,
    VerifiedEvidenceContext,
)
from app.services.llm_client import generate_explanation


def _canonicalize_number(value):
    """
    Remove meaningless floating-point representation noise while
    preserving meaningful numeric precision.

    Examples:
        0.9999999999999999 -> 1.0
        74.46800000000001 -> 74.468
        1.4857e-07 -> 1.4857e-07

    Integers and booleans are preserved unchanged.
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            return value

        return float(f"{value:.12g}")

    return value


def _canonicalize_evidence_numbers(value):
    """
    Recursively canonicalize numeric values inside verified evidence.

    This transformation is applied only to the controlled LLM evidence
    context. It does not modify the original deterministic analysis
    result or InsightContract.
    """
    if isinstance(value, dict):
        return {
            key: _canonicalize_evidence_numbers(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _canonicalize_evidence_numbers(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _canonicalize_evidence_numbers(item)
            for item in value
        ]

    return _canonicalize_number(value)



logger = logging.getLogger(__name__)

DEFAULT_LLM_AUTO_EXPLANATION_LIMIT = 3
MAX_LLM_AUTO_EXPLANATION_LIMIT = 10


def get_llm_auto_explanation_limit():
    """
    Return the maximum number of ranked insights
    that may automatically call the LLM.
    """
    raw_value = os.getenv(
        "LLM_AUTO_EXPLANATION_LIMIT",
        str(DEFAULT_LLM_AUTO_EXPLANATION_LIMIT),
    )

    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        logger.warning(
            "Invalid LLM_AUTO_EXPLANATION_LIMIT; "
            "using default=%s",
            DEFAULT_LLM_AUTO_EXPLANATION_LIMIT,
        )
        return DEFAULT_LLM_AUTO_EXPLANATION_LIMIT

    return max(
        0,
        min(
            value,
            MAX_LLM_AUTO_EXPLANATION_LIMIT,
        ),
    )

def build_verified_evidence_context(insight):
    """Return the only fields that are permitted to cross the LLM boundary."""
    if insight.get("verification", {}).get("status") != "verified":
        raise ValueError(
            "Only verified insights can be explained."
        )

    context = VerifiedEvidenceContext(
        insight_type=insight["insight_type"],
        title=insight.get("title", ""),
        source_columns=deepcopy(
            insight.get("source_columns", [])
        ),
        method=insight.get("method", ""),
        evidence=deepcopy(
            insight.get("evidence", {})
        ),
        verification=deepcopy(
            insight.get("verification", {})
        ),
        limitations=deepcopy(
            insight.get("limitations", [])
        ),
    )

    context_data = context.model_dump()

    return _canonicalize_evidence_numbers(
        context_data
    )


def build_explanation_prompt(verified_evidence):
    return {
        "role": "system",
        "instruction": (
            "Explain the provided business insight clearly for a business user. "
            "Use only numbers present in the evidence or verification. "
            "Preserve every numeric value exactly as provided, including all digits "
            "and scale. Do not convert units, divide or multiply values, express "
            "thousands as shorter values, calculate, estimate, round, or invent "
            "numbers. For example, if the evidence contains 82000, the explanation "
            "must say 82000, not 82. Do not make causal claims from correlation. "
            "Mention important limitations when relevant."
        ),
        "verified_evidence": deepcopy(
            verified_evidence
        ),
    }


def validate_explanation(
    explanation,
    insight,
):
    from app.services.numeric_guardrail import (
        validate_explanation_numbers,
    )

    return validate_explanation_numbers(
        explanation,
        insight,
    )


def explain_insight(
    insight,
    llm_function=None,
):
    try:
        verified_evidence = (
            build_verified_evidence_context(
                insight
            )
        )
    except ValueError:
        return {
            "status": "rejected",
            "explanation": None,
            "validation": {
                "valid": False,
                "reason": (
                    "insight_not_verified"
                ),
                "unsupported_numbers": [],
            },
        }

    prompt = build_explanation_prompt(
        verified_evidence
    )

    try:
        response = generate_explanation(
            prompt,
            llm_function,
        )
    except Exception as exc:
        status_code = (
            getattr(exc, "code", None)
            or getattr(
                exc,
                "status_code",
                None,
            )
        )

        logger.warning(
            "LLM explanation provider unavailable: "
            "type=%s status=%s",
            type(exc).__name__,
            status_code,
        )

        return {
            "status": "unavailable",
            "explanation": None,
            "validation": {
                "valid": False,
                "reason": "llm_unavailable",
                "unsupported_numbers": [],
            },
        }

    try:
        explanation = (
            ExplanationResponse.model_validate(
                response
            )
        )
    except ValidationError:
        return {
            "status": "rejected",
            "explanation": None,
            "validation": {
                "valid": False,
                "reason": "invalid_response",
                "unsupported_numbers": [],
            },
        }

    if not explanation.text.strip():
        return {
            "status": "rejected",
            "explanation": None,
            "validation": {
                "valid": False,
                "reason": "invalid_response",
                "unsupported_numbers": [],
            },
        }

    explanation_data = (
        explanation.model_dump()
    )

    validation = validate_explanation(
        explanation_data,
        verified_evidence,
    )

    if not validation["valid"]:
        return {
            "status": "rejected",
            "explanation": None,
            "validation": validation,
        }

    return {
        "status": "approved",
        "explanation": explanation_data,
        "validation": validation,
    }



def _deterministic_explanation_text(
    verified_evidence,
):
    """
    Build a human-readable explanation only from
    the already verified evidence boundary.

    This function performs no new analytics and
    makes no external API call.
    """
    insight_type = verified_evidence.get(
        "insight_type"
    )

    evidence = verified_evidence.get(
        "evidence",
        {},
    )

    source_columns = verified_evidence.get(
        "source_columns",
        [],
    )

    limitations = verified_evidence.get(
        "limitations",
        [],
    )

    parts = []

    if insight_type == "time_series_trend":
        measure = (
            source_columns[0]
            if source_columns
            else "The measure"
        )

        direction = evidence.get(
            "trend_direction"
        )

        strength = evidence.get(
            "trend_strength"
        )

        if direction:
            if strength:
                parts.append(
                    f"{measure} has a verified "
                    f"{strength} {direction} "
                    "historical trend."
                )
            else:
                parts.append(
                    f"{measure} has a verified "
                    f"{direction} historical trend."
                )

        first_date = evidence.get(
            "first_date"
        )
        first_value = evidence.get(
            "first_value"
        )
        last_date = evidence.get(
            "last_date"
        )
        last_value = evidence.get(
            "last_value"
        )

        if (
            first_date is not None
            and first_value is not None
            and last_date is not None
            and last_value is not None
        ):
            parts.append(
                f"The verified series moves from "
                f"{first_value} on {first_date} "
                f"to {last_value} on {last_date}."
            )

        percentage_change = evidence.get(
            "percentage_change"
        )

        if percentage_change is not None:
            parts.append(
                "The verified overall percentage "
                f"change is {percentage_change}%."
            )

        r_squared = evidence.get(
            "r_squared"
        )

        if r_squared is not None:
            parts.append(
                "The verified R-squared value is "
                f"{r_squared}."
            )

    elif insight_type == "correlation":
        first_column = (
            source_columns[0]
            if len(source_columns) > 0
            else "the first variable"
        )

        second_column = (
            source_columns[1]
            if len(source_columns) > 1
            else "the second variable"
        )

        correlation = evidence.get(
            "correlation"
        )

        sample_size = evidence.get(
            "sample_size"
        )

        p_value = evidence.get(
            "p_value"
        )

        if correlation is not None:
            parts.append(
                "The verified correlation between "
                f"{first_column} and "
                f"{second_column} is "
                f"{correlation}."
            )

        if sample_size is not None:
            parts.append(
                "The relationship is based on "
                f"{sample_size} observations."
            )

        if p_value is not None:
            parts.append(
                "The verified p-value is "
                f"{p_value}."
            )

        parts.append(
            "This relationship is an association "
            "and does not establish causation."
        )

    elif insight_type == "group_difference":
        highest_group = evidence.get(
            "highest_group"
        )

        highest_value = evidence.get(
            "highest_value"
        )

        lowest_group = evidence.get(
            "lowest_group"
        )

        lowest_value = evidence.get(
            "lowest_value"
        )

        absolute_difference = evidence.get(
            "absolute_difference"
        )

        percentage_difference = evidence.get(
            "percentage_difference"
        )

        if (
            highest_group is not None
            and highest_value is not None
        ):
            parts.append(
                f"{highest_group} has a verified "
                f"average value of {highest_value}."
            )

        if (
            lowest_group is not None
            and lowest_value is not None
        ):
            parts.append(
                f"{lowest_group} has a verified "
                f"average value of {lowest_value}."
            )

        if absolute_difference is not None:
            parts.append(
                "The verified absolute difference "
                f"is {absolute_difference}."
            )

        if percentage_difference is not None:
            parts.append(
                "The verified percentage difference "
                f"is {percentage_difference}%."
            )

        parts.append(
            "A difference between groups does not "
            "by itself establish causation."
        )

    elif insight_type == "outlier":
        measure = (
            source_columns[0]
            if source_columns
            else "The measure"
        )

        outlier_count = evidence.get(
            "outlier_count"
        )

        lower_bound = evidence.get(
            "lower_bound"
        )

        upper_bound = evidence.get(
            "upper_bound"
        )

        if outlier_count is not None:
            parts.append(
                f"{measure} contains "
                f"{outlier_count} verified "
                "IQR outlier observations."
            )

        if (
            lower_bound is not None
            and upper_bound is not None
        ):
            parts.append(
                "The verified IQR bounds are "
                f"{lower_bound} to "
                f"{upper_bound}."
            )

        parts.append(
            "An outlier is not automatically a "
            "data error and should be reviewed "
            "in business context."
        )

    else:
        title = verified_evidence.get(
            "title",
            "This insight",
        )

        parts.append(
            f"{title}. This insight passed "
            "deterministic verification."
        )

    if limitations:
        parts.append(
            "Limitation: "
            + str(limitations[0])
        )

    return " ".join(parts)


def build_deterministic_explanation(
    insight,
):
    """
    Produce a guarded local explanation without
    contacting Gemini or any external provider.
    """
    try:
        verified_evidence = (
            build_verified_evidence_context(
                insight
            )
        )
    except ValueError:
        return {
            "status": "rejected",
            "explanation": None,
            "validation": {
                "valid": False,
                "reason": (
                    "insight_not_verified"
                ),
                "unsupported_numbers": [],
            },
        }

    explanation_data = {
        "text": (
            _deterministic_explanation_text(
                verified_evidence
            )
        )
    }

    validation = validate_explanation(
        explanation_data,
        verified_evidence,
    )

    if not validation["valid"]:
        return {
            "status": "rejected",
            "explanation": None,
            "validation": validation,
        }

    return {
        "status": "approved",
        "explanation": explanation_data,
        "validation": validation,
        "source": "deterministic",
    }


def explain_ranked_insights(
    ranked_insights,
    ai_limit=3,
):
    """
    Limit external LLM usage while keeping every
    ranked verified insight explainable.

    Ranks within ai_limit receive one LLM attempt.
    Any failed/rejected LLM result falls back to
    the deterministic explanation.

    Remaining ranks never contact the LLM.
    """
    explained_insights = []

    for rank, insight in enumerate(
        ranked_insights,
        start=1,
    ):
        if rank <= ai_limit:
            explanation = explain_insight(
                insight
            )

            if (
                explanation.get("status")
                != "approved"
            ):
                explanation = (
                    build_deterministic_explanation(
                        insight
                    )
                )
            else:
                explanation = {
                    **explanation,
                    "source": "llm",
                }

        else:
            explanation = (
                build_deterministic_explanation(
                    insight
                )
            )

        explained_insights.append(
            {
                **insight,
                "explanation": explanation,
            }
        )

    return explained_insights


def mock_llm(prompt):
    insight = prompt[
        "verified_evidence"
    ]

    insight_type = insight.get(
        "insight_type"
    )

    if insight_type == "correlation":
        evidence = insight.get(
            "evidence",
            {},
        )

        source_columns = insight.get(
            "source_columns",
            [],
        )

        column_a = (
            source_columns[0]
            if len(source_columns) > 0
            else "first variable"
        )

        column_b = (
            source_columns[1]
            if len(source_columns) > 1
            else "second variable"
        )

        correlation = evidence.get(
            "correlation"
        )

        p_value = evidence.get(
            "p_value"
        )

        sample_size = evidence.get(
            "sample_size"
        )

        return {
            "text": (
                f"{column_a} and {column_b} show a strong positive "
                f"relationship in the observed data. "
                f"The correlation is {correlation}, based on "
                f"{sample_size} observations, with a p-value of "
                f"{p_value}. "
                f"This indicates that higher values of {column_a} "
                f"tend to be associated with higher values of "
                f"{column_b} in this dataset. "
                f"However, this is a correlation and does not "
                f"establish that one variable causes the other."
            )
        }

    return {
        "text": (
            "This insight is based on the available analysis "
            "evidence and has passed deterministic verification."
        )
    }