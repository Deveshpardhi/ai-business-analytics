import csv
import io
import json
from datetime import date, datetime
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter


CSV_HEADERS = [
    "rank",
    "insight_type",
    "title",
    "source_columns",
    "method",
    "verification_status",
    "confidence_level",
    "confidence_score",
    "priority_score",
    "evidence",
    "limitations",
    "explanation_status",
    "explanation",
    "recommendation_action",
    "recommendation_reason",
    "recommendation_priority",
]


def _insight_key(insight: dict) -> tuple:
    return (
        insight.get("insight_type"),
        insight.get("method"),
        tuple(insight.get("source_columns", [])),
        insight.get("title"),
    )


def _spreadsheet_safe(value: Any) -> Any:
    """
    Prevent CSV / spreadsheet formula injection.

    Numeric values remain numeric. Strings beginning with spreadsheet
    formula-control characters are prefixed with an apostrophe.
    """
    if value is None:
        return ""

    if isinstance(value, (int, float, bool)):
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (dict, list, tuple)):
        value = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
    else:
        value = str(value)

    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value

    return value


def _build_lookup(items: list[dict] | None) -> dict:
    return {
        _insight_key(item): item
        for item in (items or [])
    }


def build_verified_insight_rows(
    ranked_insights: list[dict] | None,
    explained_insights: list[dict] | None = None,
    recommended_insights: list[dict] | None = None,
) -> list[dict]:
    """
    Build export rows strictly from already-ranked verified insights.

    Raw analysis results and uploaded dataset rows are intentionally
    not accepted by this function.
    """
    explanations = _build_lookup(
        explained_insights
    )

    recommendations = _build_lookup(
        recommended_insights
    )

    rows = []

    for rank, insight in enumerate(
        ranked_insights or [],
        start=1,
    ):
        key = _insight_key(insight)

        explained = explanations.get(
            key,
            {},
        )

        recommended = recommendations.get(
            key,
            {},
        )

        explanation = explained.get(
            "explanation",
            {},
        ) or {}

        recommendation = recommended.get(
            "recommendation",
            {},
        ) or {}

        recommendation_content = (
            recommendation.get(
                "recommendation",
                {},
            )
            if isinstance(
                recommendation.get(
                    "recommendation"
                ),
                dict,
            )
            else recommendation
        )

        confidence = insight.get(
            "confidence",
            {},
        ) or {}

        verification = insight.get(
            "verification",
            {},
        ) or {}

        rows.append({
            "rank": rank,
            "insight_type": insight.get(
                "insight_type"
            ),
            "title": insight.get(
                "title"
            ),
            "source_columns": ", ".join(
                str(column)
                for column in insight.get(
                    "source_columns",
                    [],
                )
            ),
            "method": insight.get(
                "method"
            ),
            "verification_status": (
                verification.get(
                    "status"
                )
            ),
            "confidence_level": (
                confidence.get(
                    "level"
                )
            ),
            "confidence_score": (
                confidence.get(
                    "score"
                )
            ),
            "priority_score": (
                insight.get(
                    "score"
                )
            ),
            "evidence": insight.get(
                "evidence",
                {},
            ),
            "limitations": insight.get(
                "limitations",
                [],
            ),
            "explanation_status": (
                explanation.get(
                    "status"
                )
                if isinstance(
                    explanation,
                    dict,
                )
                else None
            ),
            "explanation": (
                explanation.get(
                    "explanation",
                    {},
                ).get(
                    "text"
                )
                if isinstance(
                    explanation,
                    dict,
                )
                and isinstance(
                    explanation.get(
                        "explanation"
                    ),
                    dict,
                )
                else ""
            ),
            "recommendation_action": (
                recommendation_content.get(
                    "action"
                )
                if isinstance(
                    recommendation_content,
                    dict,
                )
                else ""
            ),
            "recommendation_reason": (
                recommendation_content.get(
                    "reason"
                )
                if isinstance(
                    recommendation_content,
                    dict,
                )
                else ""
            ),
            "recommendation_priority": (
                recommendation_content.get(
                    "priority"
                )
                if isinstance(
                    recommendation_content,
                    dict,
                )
                else ""
            ),
        })

    return rows


def build_csv_export(
    ranked_insights: list[dict] | None,
    explained_insights: list[dict] | None = None,
    recommended_insights: list[dict] | None = None,
) -> bytes:
    rows = build_verified_insight_rows(
        ranked_insights,
        explained_insights,
        recommended_insights,
    )

    buffer = io.StringIO(
        newline=""
    )

    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_HEADERS,
    )

    writer.writeheader()

    for row in rows:
        writer.writerow({
            key: _spreadsheet_safe(
                row.get(key)
            )
            for key in CSV_HEADERS
        })

    return buffer.getvalue().encode(
        "utf-8-sig"
    )


def _write_table(
    worksheet,
    headers,
    rows,
):
    worksheet.append(headers)

    for cell in worksheet[1]:
        cell.font = Font(
            bold=True
        )

    for row in rows:
        worksheet.append([
            _spreadsheet_safe(
                value
            )
            for value in row
        ])

    worksheet.freeze_panes = "A2"

    if worksheet.max_row >= 1:
        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

    for column_index, column in enumerate(
        worksheet.columns,
        start=1,
    ):
        width = 10

        for cell in column:
            value = cell.value

            if value is None:
                continue

            width = max(
                width,
                min(
                    len(str(value)) + 2,
                    48,
                ),
            )

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

        worksheet.column_dimensions[
            get_column_letter(
                column_index
            )
        ].width = width


def build_xlsx_export(
    *,
    run_id,
    dataset_version_id,
    status,
    created_at,
    ranked_insights,
    explained_insights,
    recommended_insights,
) -> bytes:
    rows = build_verified_insight_rows(
        ranked_insights,
        explained_insights,
        recommended_insights,
    )

    workbook = Workbook()

    summary = workbook.active
    summary.title = "Executive Summary"

    high = sum(
        1
        for row in rows
        if row["confidence_level"]
        == "high"
    )

    medium = sum(
        1
        for row in rows
        if row["confidence_level"]
        == "medium"
    )

    low = sum(
        1
        for row in rows
        if row["confidence_level"]
        == "low"
    )

    top = rows[0] if rows else {}

    summary_rows = [
        (
            "Verified signals",
            len(rows),
        ),
        (
            "High confidence",
            high,
        ),
        (
            "Medium confidence",
            medium,
        ),
        (
            "Low confidence",
            low,
        ),
        (
            "Top finding",
            top.get(
                "title",
                "No ranked insight",
            ),
        ),
        (
            "Top priority score",
            top.get(
                "priority_score",
                "",
            ),
        ),
    ]

    _write_table(
        summary,
        [
            "Metric",
            "Value",
        ],
        summary_rows,
    )

    verified = workbook.create_sheet(
        "Verified Insights"
    )

    verified_headers = [
        "Rank",
        "Insight Type",
        "Title",
        "Source Columns",
        "Method",
        "Verification",
        "Confidence Level",
        "Confidence Score",
        "Priority Score",
        "Limitations",
        "Grounded Explanation",
        "Recommendation",
        "Recommendation Reason",
        "Recommendation Priority",
    ]

    verified_rows = [
        [
            row["rank"],
            row["insight_type"],
            row["title"],
            row["source_columns"],
            row["method"],
            row["verification_status"],
            row["confidence_level"],
            row["confidence_score"],
            row["priority_score"],
            row["limitations"],
            row["explanation"],
            row["recommendation_action"],
            row["recommendation_reason"],
            row["recommendation_priority"],
        ]
        for row in rows
    ]

    _write_table(
        verified,
        verified_headers,
        verified_rows,
    )

    evidence_sheet = (
        workbook.create_sheet(
            "Evidence"
        )
    )

    evidence_rows = []

    for row in rows:
        evidence = row.get(
            "evidence",
            {},
        )

        if not isinstance(
            evidence,
            dict,
        ):
            continue

        for field, value in evidence.items():
            evidence_rows.append([
                row["rank"],
                row["title"],
                field,
                value,
            ])

    _write_table(
        evidence_sheet,
        [
            "Rank",
            "Insight",
            "Evidence Field",
            "Evidence Value",
        ],
        evidence_rows,
    )

    metadata = workbook.create_sheet(
        "Run Metadata"
    )

    metadata_rows = [
        (
            "Analysis Run ID",
            str(run_id),
        ),
        (
            "Dataset Version ID",
            str(dataset_version_id),
        ),
        (
            "Run Status",
            status,
        ),
        (
            "Created At",
            (
                created_at.isoformat()
                if hasattr(
                    created_at,
                    "isoformat",
                )
                else created_at
            ),
        ),
        (
            "Export Scope",
            (
                "Ranked verified insights, "
                "grounded explanations, "
                "recommendations, and run metadata only"
            ),
        ),
        (
            "Raw Dataset Included",
            "No",
        ),
        (
            "Protected / PII Columns Included",
            "No",
        ),
    ]

    _write_table(
        metadata,
        [
            "Field",
            "Value",
        ],
        metadata_rows,
    )

    output = io.BytesIO()
    workbook.save(output)

    return output.getvalue()
