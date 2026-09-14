from app.services.llm_client import generate_explanation


def build_explanation_prompt(insight):
    return {
        "role": "system",
        "instruction": (
            "Explain the provided business insight clearly for a business user. "
            "Use only numbers present in the evidence or verification. "
            "Do not calculate, estimate, round, or invent numbers. "
            "Do not make causal claims from correlation. "
            "Mention important limitations when relevant."
        ),
        "insight": insight,
    }


def validate_explanation(explanation, insight):
    from app.services.numeric_guardrail import (
        validate_explanation_numbers,
    )

    return validate_explanation_numbers(
        explanation,
        insight,
    )


def explain_insight(insight, llm_function):
    prompt = build_explanation_prompt(insight)

    explanation = generate_explanation(
        prompt,
        llm_function,
    )

    validation = validate_explanation(
        explanation,
        insight,
    )

    if not validation["valid"]:
        return {
            "status": "rejected",
            "explanation": None,
            "validation": validation,
        }

    return {
        "status": "approved",
        "explanation": explanation,
        "validation": validation,
    }


def mock_llm(prompt):
    insight = prompt["insight"]

    insight_type = insight.get("insight_type")

    if insight_type == "correlation":
        evidence = insight.get("evidence", {})
        verification = insight.get("verification", {})

        source_columns = insight.get("source_columns", [])

        column_a = source_columns[0] if len(source_columns) > 0 else "first variable"
        column_b = source_columns[1] if len(source_columns) > 1 else "second variable"
        correlation = evidence.get("correlation")
        p_value = evidence.get("p_value")
        sample_size = evidence.get("sample_size")

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