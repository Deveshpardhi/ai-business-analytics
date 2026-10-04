import { useMemo, useRef, useState } from "react";

import {
  analyzeDataset,
  loadAnalysisRuns,
  loadDatasetOverview,
  loadDatasetPlan,
  uploadDataset,
} from "./api";

const supportedExtensions = ["csv", "xlsx", "xls"];


function formatValue(value) {
  if (value === null || value === undefined) {
    return "Not available";
  }

  if (Array.isArray(value)) {
    return value.join(", ");
  }

  if (typeof value === "number") {
    return Number.isInteger(value)
      ? value.toString()
      : value.toPrecision(5);
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}


function StatusPill({
  tone = "neutral",
  children,
}) {
  return (
    <span className={`pill ${tone}`}>
      {children}
    </span>
  );
}


function TrustPanel() {
  return (
    <aside className="trust-panel">
      <p className="eyebrow">
        Trust by design
      </p>

      <h2>
        Evidence first. AI second.
      </h2>

      <ul>
        <li>
          <span>01</span>
          Numbers come from deterministic analysis.
        </li>

        <li>
          <span>02</span>
          Only verified insights reach this dashboard.
        </li>

        <li>
          <span>03</span>
          AI explains approved evidence; it does not calculate it.
        </li>
      </ul>
    </aside>
  );
}


function DatasetOverview({
  upload,
  overview,
}) {
  const semanticColumns = Object.entries(
    overview.semantics?.columns ?? {}
  );

  const protectedColumns = Object.entries(
    overview.pii?.protected_columns ?? {}
  );

  return (
    <section className="overview card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            Dataset overview
          </p>

          <h2>
            {upload.file_name}
          </h2>
        </div>

        <StatusPill
          tone={
            overview.validation.valid
              ? "success"
              : "danger"
          }
        >
          {overview.validation.valid
            ? "Validated"
            : "Validation needs attention"}
        </StatusPill>
      </div>

      <div className="stats-grid">
        <div>
          <strong>
            {overview.validation.rows}
          </strong>

          <span>
            Rows
          </span>
        </div>

        <div>
          <strong>
            {overview.validation.columns}
          </strong>

          <span>
            Columns
          </span>
        </div>

        <div>
          <strong>
            {semanticColumns.length}
          </strong>

          <span>
            Safe columns profiled
          </span>
        </div>
      </div>

      {overview.validation.warnings?.length > 0 && (
        <div className="notice warning">
          <strong>
            Data quality notes
          </strong>

          <span>
            {overview.validation.warnings.join(" ")}
          </span>
        </div>
      )}

      {protectedColumns.length > 0 ? (
        <div className="notice protected">
          <strong>
            PII gate active
          </strong>

          <span>
            {protectedColumns
              .map(
                ([column, type]) =>
                  `${column} (${type})`
              )
              .join(", ")}{" "}
            will be excluded from profiling and analysis.
          </span>
        </div>
      ) : (
        <div className="notice success">
          <strong>
            PII scan complete
          </strong>

          <span>
            No protected columns were detected.
          </span>
        </div>
      )}

      <div className="role-list">
        <h3>
          Detected semantic roles
        </h3>

        {semanticColumns.length ? (
          semanticColumns.map(
            ([name, detail]) => (
              <div
                className="role-row"
                key={name}
              >
                <span>
                  {name}
                </span>

                <StatusPill>
                  {detail.role}
                </StatusPill>

                <small>
                  {detail.dtype} ·{" "}
                  {detail.unique_count} unique
                </small>
              </div>
            )
          )
        ) : (
          <p className="muted">
            No safe columns are available for semantic analysis.
          </p>
        )}
      </div>
    </section>
  );
}


function PlanSummary({
  plan,
}) {
  if (!plan) {
    return null;
  }

  const analyses = plan.analyses ?? [];

  const counts = analyses.reduce(
    (result, analysis) => {
      const type = analysis.type;

      result[type] =
        (result[type] ?? 0) + 1;

      return result;
    },
    {}
  );

  return (
    <section className="card plan-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            Deterministic analysis plan
          </p>

          <h2>
            {analyses.length} analyses prepared
          </h2>
        </div>

        <StatusPill tone="success">
          Planner ready
        </StatusPill>
      </div>

      <div className="plan-stats">
        <div>
          <strong>
            {counts.descriptive_statistics ?? 0}
          </strong>

          <span>
            Descriptive
          </span>
        </div>

        <div>
          <strong>
            {counts.group_comparison ?? 0}
          </strong>

          <span>
            Group comparisons
          </span>
        </div>

        <div>
          <strong>
            {counts.correlation ?? 0}
          </strong>

          <span>
            Correlations
          </span>
        </div>

        <div>
          <strong>
            {counts.time_series ?? 0}
          </strong>

          <span>
            Time series
          </span>
        </div>
      </div>

      <div className="plan-columns">
        <div>
          <h3>
            Measures
          </h3>

          <p>
            {plan.measures?.length
              ? plan.measures.join(", ")
              : "None"}
          </p>
        </div>

        <div>
          <h3>
            Dimensions
          </h3>

          <p>
            {plan.dimensions?.length
              ? plan.dimensions.join(", ")
              : "None"}
          </p>
        </div>

        <div>
          <h3>
            Dates
          </h3>

          <p>
            {plan.dates?.length
              ? plan.dates.join(", ")
              : "None"}
          </p>
        </div>

        <div>
          <h3>
            Identifiers excluded
          </h3>

          <p>
            {plan.identifiers?.length
              ? plan.identifiers.join(", ")
              : "None"}
          </p>
        </div>
      </div>
    </section>
  );
}


function AnalysisRunHistory({
  history,
}) {
  const runs =
    history?.analysis_runs ?? [];

  if (!runs.length) {
    return null;
  }

  return (
    <section className="card run-history">
      <div className="section-heading">
        <div>
          <p className="eyebrow">
            Analysis history
          </p>

          <h2>
            Previous runs
          </h2>
        </div>

        <StatusPill>
          {history.count} total
        </StatusPill>
      </div>

      <div className="run-list">
        {runs.map((run) => (
          <div
            className="run-row"
            key={run.id}
          >
            <div>
              <strong>
                {run.id}
              </strong>

              <small>
                {run.created_at
                  ? new Date(
                      run.created_at
                    ).toLocaleString()
                  : "Time unavailable"}
              </small>
            </div>

            <StatusPill
              tone={
                run.status === "completed"
                  ? "success"
                  : run.status ===
                      "partially_completed"
                    ? "warning"
                    : "danger"
              }
            >
              {run.status?.replaceAll(
                "_",
                " "
              )}
            </StatusPill>
          </div>
        ))}
      </div>
    </section>
  );
}


function EvidenceVisual({
  insight,
}) {
  const evidence =
    insight.evidence ?? {};

  if (
    insight.insight_type === "correlation" &&
    typeof evidence.correlation === "number"
  ) {
    const width = Math.min(
      100,
      Math.abs(
        evidence.correlation
      ) * 100
    );

    return (
      <div className="evidence-visual">
        <div className="visual-label">
          <span>
            Correlation strength
          </span>

          <strong>
            {formatValue(
              evidence.correlation
            )}
          </strong>
        </div>

        <div className="bar-track">
          <div
            className="bar-fill"
            style={{
              width: `${width}%`,
            }}
          />
        </div>
      </div>
    );
  }

  if (
    insight.insight_type === "outlier" &&
    evidence.outliers?.length
  ) {
    return (
      <div className="outlier-list">
        {evidence.outliers.map(
          (value, index) => (
            <span
              key={`${value}-${index}`}
            >
              {formatValue(value)}
            </span>
          )
        )}
      </div>
    );
  }

  return null;
}


function InsightCard({
  insight,
  explanation,
  recommendation,
}) {
  const evidence = Object.entries(
    insight.evidence ?? {}
  ).filter(
    ([, value]) =>
      value !== null &&
      value !== undefined
  );

  const confidence =
    insight.confidence ?? {};

  return (
    <article className="insight-card">
      <div className="insight-topline">
        <StatusPill tone="dark">
          {insight.insight_type.replaceAll(
            "_",
            " "
          )}
        </StatusPill>

        <StatusPill tone="success">
          Verified
        </StatusPill>
      </div>

      <h3>
        {insight.title}
      </h3>

      <p className="source-columns">
        {insight.source_columns?.join(
          " · "
        )}
      </p>

      <EvidenceVisual
        insight={insight}
      />

      <dl className="evidence-grid">
        {evidence.map(
          ([key, value]) => (
            <div key={key}>
              <dt>
                {key.replaceAll(
                  "_",
                  " "
                )}
              </dt>

              <dd>
                {formatValue(
                  value
                )}
              </dd>
            </div>
          )
        )}
      </dl>

      <div className="confidence-row">
        <span>
          Confidence
        </span>

        <strong>
          {confidence.level ??
            "Not available"}

          {typeof confidence.score ===
          "number"
            ? ` · ${formatValue(
                confidence.score
              )}`
            : ""}
        </strong>
      </div>

      <div className="explanation-block">
        <h4>
          Grounded explanation
        </h4>

        {explanation?.status ===
        "approved" ? (
          <p>
            {
              explanation.explanation
                .text
            }
          </p>
        ) : (
          <p className="muted">
            {explanation?.status ===
            "unavailable"
              ? "Explanation is currently unavailable. The verified analytical evidence remains available above."
              : "No approved explanation is available for this insight."}
          </p>
        )}
      </div>

      {recommendation?.recommendation && (
        <div className="recommendation-block">
          <h4>
            Recommended next step
          </h4>

          <p>
            {
              recommendation
                .recommendation
                .action
            }
          </p>

          <small>
            {
              recommendation
                .recommendation
                .reason
            }
          </small>
        </div>
      )}
    </article>
  );
}


function ResultsDashboard({
  analysis,
}) {
  const insights =
    analysis.ranked_insights ?? [];

  const explanationByTitle =
    useMemo(
      () =>
        new Map(
          (
            analysis.explained_insights ??
            []
          ).map((item) => [
            item.title,
            item.explanation,
          ])
        ),
      [analysis]
    );

  const recommendationByTitle =
    useMemo(
      () =>
        new Map(
          (
            analysis.recommended_insights ??
            []
          ).map((item) => [
            item.title,
            item.recommendation,
          ])
        ),
      [analysis]
    );

  return (
    <section className="results">
      <div className="results-header">
        <div>
          <p className="eyebrow">
            Analysis results
          </p>

          <h2>
            Verified business signals
          </h2>

          <p>
            Only insights that passed deterministic verification are shown.
          </p>

          {analysis.analysis_run_id && (
            <p className="run-id">
              Analysis run ·{" "}
              {analysis.analysis_run_id}
            </p>
          )}
        </div>

        <StatusPill
          tone={
            analysis.status ===
            "completed"
              ? "success"
              : "warning"
          }
        >
          {analysis.status?.replaceAll(
            "_",
            " "
          )}
        </StatusPill>
      </div>

      {insights.length ? (
        <div className="insight-grid">
          {insights.map(
            (insight) => (
              <InsightCard
                key={`${insight.insight_type}-${insight.title}`}
                insight={insight}
                explanation={explanationByTitle.get(
                  insight.title
                )}
                recommendation={recommendationByTitle.get(
                  insight.title
                )}
              />
            )
          )}
        </div>
      ) : (
        <div className="empty-state">
          <h3>
            No verified insights were found
          </h3>

          <p>
            The dataset completed analysis, but no discovered insight met the verification threshold.
          </p>
        </div>
      )}
    </section>
  );
}


export default function App() {
  const fileInput =
    useRef(null);

  const [
    upload,
    setUpload,
  ] = useState(null);

  const [
    overview,
    setOverview,
  ] = useState(null);

  const [
    plan,
    setPlan,
  ] = useState(null);

  const [
    analysis,
    setAnalysis,
  ] = useState(null);

  const [
    history,
    setHistory,
  ] = useState(null);

  const [
    state,
    setState,
  ] = useState("idle");

  const [
    error,
    setError,
  ] = useState("");


  async function handleFile(file) {
    if (!file) {
      return;
    }

    const extension = file.name
      .split(".")
      .pop()
      ?.toLowerCase();

    if (
      !supportedExtensions.includes(
        extension
      )
    ) {
      setError(
        "Choose a CSV, XLSX, or XLS file."
      );

      return;
    }

    setError("");
    setAnalysis(null);
    setOverview(null);
    setUpload(null);
    setPlan(null);
    setHistory(null);

    setState("uploading");

    try {
      const uploaded =
        await uploadDataset(file);

      setUpload(uploaded);

      setState("inspecting");

      const [
        nextOverview,
        nextPlan,
      ] = await Promise.all([
        loadDatasetOverview(
          uploaded.dataset_version_id
        ),

        loadDatasetPlan(
          uploaded.dataset_version_id
        ),
      ]);

      setOverview(
        nextOverview
      );

      setPlan(
        nextPlan
      );

      setState("ready");
    } catch (nextError) {
      setState("idle");

      setError(
        nextError.message
      );
    }
  }


  async function handleAnalyze() {
    if (
      !upload ||
      !overview?.validation.valid
    ) {
      return;
    }

    setError("");
    setState("analyzing");

    try {
      const result =
        await analyzeDataset(
          upload.dataset_version_id
        );

      setAnalysis({
        ...result.analysis,
        analysis_run_id:
          result.analysis_run_id,
      });

      const nextHistory =
        await loadAnalysisRuns(
          upload.dataset_version_id
        );

      setHistory(
        nextHistory
      );

      setState("complete");
    } catch (nextError) {
      setState("ready");

      setError(
        nextError.message
      );
    }
  }


  return (
    <main>
      <nav>
        <a
          className="brand"
          href="#top"
        >
          Signal
          <span>
            Ledger
          </span>
        </a>

        <span className="nav-note">
          Trustworthy AI business analytics
        </span>
      </nav>

      <section
        className="hero"
        id="top"
      >
        <div>
          <p className="eyebrow">
            Business intelligence, grounded in evidence
          </p>

          <h1>
            Find the signal.
            <br />

            <em>
              Keep the proof.
            </em>
          </h1>

          <p className="hero-copy">
            Upload a business dataset to discover verified insights, practical next steps, and AI explanations grounded in deterministic analysis.
          </p>

          <div className="upload-card">
            <input
              ref={fileInput}
              id="dataset-file"
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(event) =>
                handleFile(
                  event.target
                    .files?.[0]
                )
              }
            />

            <label
              htmlFor="dataset-file"
              className="upload-button"
            >
              Choose a dataset
            </label>

            <p>
              CSV, XLSX, or XLS · maximum 25 MB
            </p>

            {state ===
              "uploading" && (
              <p className="loading">
                Uploading dataset…
              </p>
            )}

            {state ===
              "inspecting" && (
              <p className="loading">
                Running validation, PII scan, profiling, semantic detection, and analytics planning…
              </p>
            )}
          </div>
        </div>

        <TrustPanel />
      </section>

      {error && (
        <div
          className="page-notice error"
          role="alert"
        >
          <strong>
            Unable to continue
          </strong>

          <span>
            {error}
          </span>
        </div>
      )}

      {upload &&
        overview && (
          <>
            <DatasetOverview
              upload={upload}
              overview={overview}
            />

            <PlanSummary
              plan={plan}
            />

            <section className="analysis-cta card">
              <div>
                <p className="eyebrow">
                  Ready when you are
                </p>

                <h2>
                  Run verified analysis
                </h2>

                <p>
                  The deterministic plan above will now be executed. Discovered insights must pass verification before they can be ranked or explained by AI.
                </p>
              </div>

              <button
                type="button"
                onClick={
                  handleAnalyze
                }
                disabled={
                  state ===
                    "analyzing" ||
                  !overview
                    .validation
                    .valid
                }
              >
                {state ===
                "analyzing"
                  ? "Analysis running on the server…"
                  : "Run analysis"}
              </button>
            </section>

            {state ===
              "analyzing" && (
              <div className="page-notice loading">
                <strong>
                  Analysis in progress
                </strong>

                <span>
                  Waiting for the backend to return completed results. No progress is estimated or fabricated.
                </span>
              </div>
            )}
          </>
        )}

      {analysis && (
        <ResultsDashboard
          analysis={analysis}
        />
      )}

      {history && (
        <AnalysisRunHistory
          history={history}
        />
      )}

      {!upload &&
        !error && (
          <section className="empty-state initial">
            <h2>
              Start with a dataset
            </h2>

            <p>
              Your data is validated and scanned for protected columns before analysis begins.
            </p>
          </section>
        )}
    </main>
  );
}