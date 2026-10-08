# AI Business Analytics Platform

A trustworthy business analytics platform that converts uploaded business datasets into verified, explainable, and actionable insights.

The platform is designed around one core principle:

> **The LLM is never the source of numerical truth.**

All numerical analysis is performed deterministically using Python analytics libraries. Large language models are used only to explain already verified evidence.

---

## Project Overview

The AI Business Analytics Platform provides an end-to-end analytics workflow:

```text
Dataset Upload
      ↓
Validation
      ↓
PII Detection
      ↓
Protected Column Filtering
      ↓
Data Profiling
      ↓
Semantic Detection
      ↓
Analysis Planning
      ↓
Deterministic Analytics
      ↓
Insight Discovery
      ↓
Insight Verification
      ↓
Confidence Scoring
      ↓
Insight Ranking
      ↓
Grounded Explanation
      ↓
Numeric Guardrail
      ↓
Recommendation
      ↓
Reports / Exports
```

The system is designed to separate:

- numerical truth
- statistical verification
- AI explanation
- recommendations
- reporting

This prevents an LLM from inventing calculations or altering verified business metrics.

---

# Key Features

## Dataset Upload

Supported dataset formats:

- CSV
- XLSX
- XLS

The backend validates:

- file type
- file content
- upload size
- dataset structure

---

## PII Protection

The system detects and protects potentially sensitive columns before analytics are performed.

Examples include:

- email addresses
- phone numbers
- names
- personally identifiable fields

Protected columns are excluded from analytical planning where appropriate.

Raw datasets and PII are never sent to the LLM explanation layer.

---

## Data Profiling

The platform identifies useful information about each column, including:

- data type
- unique values
- missing values
- numeric ranges
- semantic roles
- likely identifiers
- dimensions
- measures
- date columns

---

## Semantic Detection

Columns are classified into analytical roles such as:

```text
Identifier
Dimension
Measure
Date
Protected / PII
```

Numeric identifier columns are prevented from being incorrectly treated as analytical measures.

---

# Analytics Engine

Analytics are calculated deterministically.

Current analytical capabilities include:

## Descriptive Statistics

Examples:

- mean
- median
- minimum
- maximum
- count
- missing values

---

## Outlier Detection

Outliers are detected using deterministic statistical methods including IQR-based analysis.

---

## Group Comparison

The platform can compare numeric measures across business dimensions.

Example:

```text
Department vs Salary
Region vs Revenue
Category vs Profit
```

Group comparisons may include:

- group averages
- highest group
- lowest group
- absolute difference
- percentage difference
- one-way ANOVA

A minimum sample requirement is enforced for statistical comparisons.

---

## Correlation Analysis

Pearson correlation is used for eligible numeric measures.

The platform calculates:

- correlation coefficient
- direction
- relationship strength
- p-value
- sample size

The system explicitly handles:

- missing pairs
- insufficient observations
- zero variance
- invalid correlation inputs

Correlation is never presented as causation.

---

## Time-Series Analysis

Time-series analytics include:

- chronological sorting
- first value
- latest value
- absolute change
- percentage change
- trend direction
- trend strength
- slope
- R²
- peak value
- trough value
- latest change
- moving averages

Time-series recommendations remain historical and do not automatically claim future prediction or causation.

---

# Insight Verification

Analytics results do not automatically become business insights.

Each discovered insight passes through a deterministic verification layer.

Verified insight structure includes:

```python
class InsightContract(BaseModel):
    insight_type: str
    title: str
    source_columns: list[str]
    method: str
    evidence: dict[str, Any]
    calculation: dict[str, Any]
    verification: dict[str, Any]
    confidence: dict[str, Any]
    limitations: list[str]
```

Only verified insights are eligible for explanation and presentation.

---

# Confidence Scoring

Insights are assigned confidence levels using deterministic rules.

Example:

```text
High
Medium
Low
```

Confidence scoring considers analytical evidence such as:

- sample size
- statistical significance
- relationship strength
- verification status
- analytical reliability

---

# Insight Ranking

Verified insights are scored and ranked so that the most relevant signals appear first.

The application currently keeps the top ranked insights for presentation.

---

# AI Explanation Layer

The LLM does not receive the raw dataset.

The LLM receives only controlled, verified evidence such as:

```text
insight_type
title
source_columns
method
evidence
verification
limitations
```

The LLM does not receive:

- raw rows
- PII
- raw calculation objects
- confidence internals
- lineage internals
- unverified insights

---

## Supported Explanation Providers

The current architecture supports:

```text
Gemini
Azure OpenAI
Mock provider
```

Provider selection is controlled through environment variables.

---

## Cost-Controlled AI Usage

Automatic AI explanation usage can be limited.

Example:

```env
LLM_AUTO_EXPLANATION_LIMIT=3
```

This means:

```text
Rank 1–3
    ↓
Attempt LLM explanation

Rank 4–10
    ↓
Use deterministic explanation
```

If the LLM fails, the application automatically uses a deterministic fallback.

---

## Deterministic Explanation Fallback

When the LLM is unavailable, overloaded, disabled, or rejected by the numeric guardrail, the platform generates a local explanation directly from verified evidence.

Example:

```text
Grounded explanation
Deterministic
```

When the LLM successfully generates an approved explanation:

```text
Grounded explanation
AI-assisted
```

The analytics workflow therefore continues even when the external AI provider is unavailable.

---

# Numeric Guardrail

Every LLM-generated explanation passes through a numeric validation layer.

The guardrail verifies that numbers used by the LLM match authoritative analytics evidence.

Unsupported numerical claims are rejected.

This protects against:

- hallucinated numbers
- modified percentages
- incorrect correlation values
- unsupported statistical claims

---

# Numeric Canonicalization

Verified evidence is canonicalized before being sent to the explanation layer.

Examples:

```text
0.9999999999999999
→
1.0
```

```text
74.46800000000001
→
74.468
```

This reduces floating-point noise while preserving authoritative analytical results.

---

# Visual Analytics

The frontend contains deterministic visualizations.

Current visualizations include:

- correlation scatter plots
- group comparison bar charts
- time-series line charts

Visualizations are produced from deterministic analytics results and not generated by an LLM.

---

# Executive Summary

The frontend produces an executive-level overview of the analysis.

It may include:

- top verified finding
- confidence distribution
- priority insights
- key business signals

The summary is based on already calculated and verified evidence.

---

# Analysis History

Analysis runs are persisted.

Users can inspect previous analysis runs for the same dataset version.

The frontend supports:

- analysis history
- run selection
- comparison between runs
- added signals
- removed signals
- changed signals

---

# Report Exports

Verified analysis reports can be exported as:

- CSV
- Excel
- PDF

Reports contain controlled analytical information such as:

- executive summary
- verified insights
- evidence
- confidence
- explanations
- recommendations
- limitations
- run metadata

Raw dataset rows and PII are not included in reporting exports.

---

# PDF Report

The PDF report includes sections such as:

```text
Signal Ledger

Verified Business Analytics Report

Run Metadata
Executive Summary
Top Finding
Verified Findings
Evidence
Grounded Explanation
Recommendations
Limitations
Trust Boundary
```

PDF generation is local and does not require an LLM API call.

---

# Architecture

```text
                        ┌─────────────────────┐
                        │       React UI      │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │     FastAPI API     │
                        └─────────┬───────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
      Dataset Services      Analysis Engine      Report Engine
              │                   │                   │
              ▼                   ▼                   ▼
      Validation / PII     Deterministic Math    CSV / XLSX / PDF
                                  │
                                  ▼
                         Insight Discovery
                                  │
                                  ▼
                         Verification Layer
                                  │
                                  ▼
                         Confidence Scoring
                                  │
                                  ▼
                          Insight Ranking
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                       ▼                     ▼
              Deterministic            LLM Explanation
              Explanation                    │
                       │                     ▼
                       │              Numeric Guardrail
                       │                     │
                       └──────────┬──────────┘
                                  ▼
                         Grounded Insight
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Polars
- SciPy
- ReportLab
- OpenPyXL
- Google Gemini SDK
- Pytest

## Frontend

- React
- Vite
- JavaScript
- Native SVG visualizations

## Infrastructure

- Docker
- Docker Compose
- PostgreSQL

---

# Repository Structure

A simplified project structure:

```text
ai-business-analytics/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── .venv/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   ├── evaluation/
│   └── ...
│
├── migrations/
├── docker-compose.yml
├── .env
├── .env.example
└── README.md
```

Actual folders may vary as the project evolves.

---

# Local Development Setup

The project is developed locally from:

```text
~/Developer/ai-business-analytics
```

Three terminals are recommended.

---

# Terminal 1 — Start Docker and PostgreSQL

Navigate to the project:

```bash
cd ~/Developer/ai-business-analytics
```

Start Docker Desktop:

```bash
open -a Docker
```

After Docker Desktop is running:

```bash
docker compose up -d
```

Check services:

```bash
docker compose ps
```

Optional Docker check:

```bash
docker ps
```

PostgreSQL should now be running.

---

# Terminal 2 — Start FastAPI Backend

Navigate to the project:

```bash
cd ~/Developer/ai-business-analytics
```

Activate the virtual environment:

```bash
source backend/.venv/bin/activate
```

Remove any temporary shell override for the LLM explanation limit:

```bash
unset LLM_AUTO_EXPLANATION_LIMIT
```

Optional configuration check:

```bash
PYTHONPATH=backend python - <<'PY'
from app.core.config import settings

print("LLM provider:", settings.llm_provider)
print("LLM model:", settings.llm_model)
print(
    "LLM auto explanation limit:",
    settings.llm_auto_explanation_limit,
)
PY
```

Start FastAPI:

```bash
uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Keep Terminal 2 running.

---

# Terminal 3 — Start React Frontend

Navigate to the frontend:

```bash
cd ~/Developer/ai-business-analytics/frontend
```

Start Vite:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

Keep Terminal 3 running.

---

# Quick Startup Reference

## Terminal 1

```bash
cd ~/Developer/ai-business-analytics

open -a Docker

docker compose up -d

docker compose ps
```

## Terminal 2

```bash
cd ~/Developer/ai-business-analytics

source backend/.venv/bin/activate

unset LLM_AUTO_EXPLANATION_LIMIT

uvicorn app.main:app \
  --app-dir backend \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

## Terminal 3

```bash
cd ~/Developer/ai-business-analytics/frontend

npm run dev
```

Then open:

```text
http://localhost:5173
```

---

# Stop the Project

## Stop Frontend

In Terminal 3:

```text
Ctrl + C
```

## Stop Backend

In Terminal 2:

```text
Ctrl + C
```

## Stop Docker Services

```bash
cd ~/Developer/ai-business-analytics

docker compose down
```

Docker volumes do not need to be removed during normal development.

---

# Environment Configuration

Create a local `.env` from `.env.example`.

Example configuration:

```env
DATABASE_URL=postgresql+psycopg2://analytics:analytics_password@localhost:5433/analytics

LLM_PROVIDER=gemini

LLM_MODEL=gemini-3.6-flash

LLM_AUTO_EXPLANATION_LIMIT=3

GEMINI_API_KEY=

AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=2024-12-01-preview

CORS_ALLOW_ORIGINS=http://localhost:5173

LOG_LEVEL=INFO
```

Never place real secrets in `.env.example`.

---

# LLM Development Modes

## Disable Automatic AI Calls

For local development without Gemini API calls:

```env
LLM_AUTO_EXPLANATION_LIMIT=0
```

All explanations will use the deterministic explanation engine.

---

## Enable AI for Top Three Insights

```env
LLM_AUTO_EXPLANATION_LIMIT=3
```

Behavior:

```text
Top 3 insights
→ LLM attempted

Remaining ranked insights
→ deterministic explanation
```

If Gemini fails:

```text
Gemini failure
→ deterministic fallback
→ analysis continues
```

---

# Configuration Validation

Configuration is centrally validated through:

```text
backend/app/core/config.py
```

Validated configuration includes:

- database URL
- supported database type
- LLM provider
- LLM model
- automatic explanation limit
- provider credentials when required
- CORS origins
- log level

Invalid configuration should fail early instead of failing during an analysis request.

---

# Structured Logging

Application logs use structured JSON logging.

Example:

```json
{
  "timestamp": "2026-10-08T12:00:00+00:00",
  "level": "INFO",
  "logger": "app.main",
  "message": "Application configuration validated",
  "event": "application_startup",
  "provider": "gemini",
  "llm_auto_limit": 3
}
```

LLM failures are logged safely.

Example:

```json
{
  "level": "WARNING",
  "event": "llm_explanation_unavailable",
  "error_type": "ServerError",
  "status": 503
}
```

Logs intentionally avoid recording:

- API keys
- raw datasets
- PII
- LLM prompts containing analytical evidence
- secrets

---

# Testing

Navigate to the project:

```bash
cd ~/Developer/ai-business-analytics
```

Activate the virtual environment:

```bash
source backend/.venv/bin/activate
```

Run the full backend test suite:

```bash
python -m pytest -q
```

---

## Run Configuration Tests

```bash
python -m pytest -q tests/test_config.py
```

---

## Run LLM Cost-Control Tests

```bash
python -m pytest -q tests/test_llm_cost_control.py
```

---

## Run Structured Logging Tests

```bash
python -m pytest -q tests/test_structured_logging.py
```

---

## Run API Workflow Tests

```bash
python -m pytest -q tests/test_api_workflow.py
```

---

## Run Golden Dataset Evaluation

```bash
python -m pytest -q tests/evaluation
```

---

# Frontend Production Build Test

Navigate to the frontend:

```bash
cd ~/Developer/ai-business-analytics/frontend
```

Run:

```bash
npm run build
```

A successful result should end with:

```text
✓ built
```

---

# Recover the Python Environment

If the project directory is moved or the environment starts using Anaconda instead of the project virtual environment, recreate the virtual environment.

```bash
cd ~/Developer/ai-business-analytics
```

Deactivate any existing virtual environment:

```bash
deactivate 2>/dev/null || true
```

Remove the stale environment:

```bash
rm -rf backend/.venv
```

Create a new environment:

```bash
python3 -m venv backend/.venv
```

Activate it:

```bash
source backend/.venv/bin/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Install pytest if necessary:

```bash
python -m pip install pytest
```

Verify Python:

```bash
which python
```

Then:

```bash
python -c "import sys; print(sys.executable)"
```

The interpreter should be inside:

```text
~/Developer/ai-business-analytics/backend/.venv/
```

---

# Verify Important Backend Dependencies

```bash
cd ~/Developer/ai-business-analytics

source backend/.venv/bin/activate
```

Then:

```bash
python - <<'PY'
import polars
import fastapi
import psycopg2
import reportlab

print("Backend dependencies OK")
PY
```

---

# Useful Git Commands

Check repository status:

```bash
git status -sb
```

View recent commits:

```bash
git log --oneline -10
```

Check differences:

```bash
git diff
```

Check staged changes:

```bash
git diff --cached
```

Push:

```bash
git push origin main
```

---

# Files That Must Not Be Committed

Never commit:

```text
.env
```

The local large Golden Dataset should also remain outside normal Git commits unless intentionally added:

```text
golden_large_business_100k.csv
```

Avoid:

```bash
git add .
```

when local files or secrets are present.

Prefer selective staging:

```bash
git add path/to/file1 path/to/file2
```

---

# Security and Trust Principles

The platform follows several important design rules.

## 1. LLMs Do Not Calculate Business Metrics

All numerical results come from deterministic Python code.

---

## 2. Only Verified Insights Reach the LLM

Unverified analytical signals cannot be explained by the LLM.

---

## 3. Raw Datasets Stay Outside the LLM Boundary

Only controlled evidence is provided to explanation providers.

---

## 4. PII Is Protected

Columns identified as sensitive are excluded where appropriate before analytics and explanation.

---

## 5. Numerical Claims Are Guarded

AI explanations must preserve authoritative numbers.

---

## 6. AI Failure Does Not Break Analytics

External LLM failure automatically falls back to deterministic explanations.

---

## 7. Correlation Does Not Imply Causation

Recommendations intentionally avoid unsupported causal claims.

---

# Example Insight

Example verified correlation result:

```text
Age and Salary have a strong positive relationship

Correlation: 0.98818
Strength: Strong
Direction: Positive
p-value: 1.7786e-9
Sample size: 12

Confidence:
High
```

Example deterministic grounded explanation:

```text
The verified correlation between Age and Salary is
0.988183685359.

The relationship is based on 12 observations.

The verified p-value is 1.7786420755e-09.

This relationship is an association and does not
establish causation.
```

The explanation does not calculate or modify the correlation.

---

# Current Project Status

Major completed areas:

- dataset upload
- validation
- PII detection
- data profiling
- semantic classification
- deterministic analytics planning
- descriptive analytics
- outlier detection
- group comparison
- ANOVA
- correlation analysis
- time-series analysis
- insight discovery
- deterministic verification
- confidence scoring
- insight ranking
- Gemini explanation provider
- Azure OpenAI explanation provider
- deterministic explanation fallback
- numeric guardrail
- LLM cost control
- explanation provenance
- executive summary
- analysis history
- run comparison
- scatter visualization
- group visualization
- time-series visualization
- CSV export
- Excel export
- PDF export
- configuration validation
- structured logging
- automated tests
- Golden Dataset evaluation

---

# Upcoming Development

Planned future work includes:

```text
Authentication
      ↓
User accounts
      ↓
Dataset ownership
      ↓
Analysis-run ownership
      ↓
Multi-user security
      ↓
Deployment hardening
      ↓
Production deployment
```

Authentication and user/data ownership are the next major application phase.

---

# Development Philosophy

This project intentionally separates:

```text
Analytics
Verification
Explanation
Recommendation
Presentation
```

The goal is not to build a chatbot that happens to analyze spreadsheets.

The goal is to build a trustworthy analytics system where:

> **Python determines the facts. AI helps communicate them.**

---

# License

This project is currently developed as a portfolio and learning project.

Licensing terms can be added before public distribution or commercial use.