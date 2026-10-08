from app.services import insight_explainer


def make_verified_insight(
    title,
):
    return {
        "insight_type": "correlation",
        "title": title,
        "source_columns": [
            "Revenue",
            "Cost",
        ],
        "method": "pearson_correlation",
        "evidence": {
            "correlation": 0.9,
            "sample_size": 10,
            "p_value": 0.01,
        },
        "calculation": {},
        "verification": {
            "status": "verified",
            "correlation": 0.9,
            "sample_size": 10,
            "p_value": 0.01,
        },
        "confidence": {
            "level": "high",
            "score": 0.9,
        },
        "limitations": [
            (
                "Correlation does not "
                "establish causation."
            )
        ],
        "score": 0.9,
    }


def test_deterministic_explanation_is_approved():
    insight = make_verified_insight(
        "Revenue and Cost are correlated"
    )

    result = (
        insight_explainer
        .build_deterministic_explanation(
            insight
        )
    )

    assert result["status"] == "approved"

    assert (
        result["source"]
        == "deterministic"
    )

    assert (
        "0.9"
        in result[
            "explanation"
        ]["text"]
    )

    assert (
        "10"
        in result[
            "explanation"
        ]["text"]
    )


def test_only_top_three_receive_llm_attempt(
    monkeypatch,
):
    insights = [
        make_verified_insight(
            f"Insight {index}"
        )
        for index in range(
            1,
            7,
        )
    ]

    llm_calls = []

    def fake_explain(insight):
        llm_calls.append(
            insight["title"]
        )

        return {
            "status": "approved",
            "explanation": {
                "text": (
                    "Verified explanation."
                )
            },
            "validation": {
                "valid": True,
                "unsupported_numbers": [],
            },
        }

    monkeypatch.setattr(
        insight_explainer,
        "explain_insight",
        fake_explain,
    )

    results = (
        insight_explainer
        .explain_ranked_insights(
            insights,
            ai_limit=3,
        )
    )

    assert len(llm_calls) == 3

    assert llm_calls == [
        "Insight 1",
        "Insight 2",
        "Insight 3",
    ]

    assert len(results) == 6

    assert (
        results[0]["explanation"]["source"]
        == "llm"
    )

    assert (
        results[2]["explanation"]["source"]
        == "llm"
    )

    assert (
        results[3]["explanation"]["source"]
        == "deterministic"
    )

    assert (
        results[5]["explanation"]["source"]
        == "deterministic"
    )


def test_llm_failure_falls_back_without_retry(
    monkeypatch,
):
    insight = make_verified_insight(
        "Revenue and Cost are correlated"
    )

    calls = []

    def unavailable_explanation(
        insight,
    ):
        calls.append(
            insight["title"]
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

    monkeypatch.setattr(
        insight_explainer,
        "explain_insight",
        unavailable_explanation,
    )

    result = (
        insight_explainer
        .explain_ranked_insights(
            [insight],
            ai_limit=3,
        )
    )

    assert len(calls) == 1

    explanation = (
        result[0]["explanation"]
    )

    assert (
        explanation["status"]
        == "approved"
    )

    assert (
        explanation["source"]
        == "deterministic"
    )


def test_rank_four_never_calls_llm(
    monkeypatch,
):
    insights = [
        make_verified_insight(
            f"Insight {index}"
        )
        for index in range(
            1,
            5,
        )
    ]

    calls = []

    def fake_explain(insight):
        calls.append(
            insight["title"]
        )

        return {
            "status": "approved",
            "explanation": {
                "text": (
                    "Verified explanation."
                )
            },
            "validation": {
                "valid": True,
                "unsupported_numbers": [],
            },
        }

    monkeypatch.setattr(
        insight_explainer,
        "explain_insight",
        fake_explain,
    )

    result = (
        insight_explainer
        .explain_ranked_insights(
            insights,
            ai_limit=3,
        )
    )

    assert len(calls) == 3

    assert (
        result[3]["explanation"]["source"]
        == "deterministic"
    )


def test_llm_auto_limit_defaults_to_three(
    monkeypatch,
):
    monkeypatch.delenv(
        "LLM_AUTO_EXPLANATION_LIMIT",
        raising=False,
    )

    assert (
        insight_explainer
        .get_llm_auto_explanation_limit()
        == 3
    )


def test_llm_auto_limit_can_be_disabled(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_AUTO_EXPLANATION_LIMIT",
        "0",
    )

    assert (
        insight_explainer
        .get_llm_auto_explanation_limit()
        == 0
    )


def test_llm_auto_limit_is_capped_at_ten(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_AUTO_EXPLANATION_LIMIT",
        "99",
    )

    assert (
        insight_explainer
        .get_llm_auto_explanation_limit()
        == 10
    )


def test_invalid_llm_auto_limit_uses_default(
    monkeypatch,
):
    monkeypatch.setenv(
        "LLM_AUTO_EXPLANATION_LIMIT",
        "invalid",
    )

    assert (
        insight_explainer
        .get_llm_auto_explanation_limit()
        == 3
    )
