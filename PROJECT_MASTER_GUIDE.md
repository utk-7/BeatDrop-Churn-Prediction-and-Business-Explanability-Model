# StreamRetain (Beat Drop) — Master Project Guide
## Churn Prediction & Business Impact Engine for a Music Streaming Service

This is the single source of truth for the project.

## 1. Project Overview
Elevator pitch: An end-to-end machine learning system that predicts which 
subscribers of a music streaming service are about to cancel, explains why in 
plain business terms, and quantifies how much revenue is at stake — so a 
Retention/Customer Success team could act on it, not just admire it.

Built on: The KKBox Churn Prediction Challenge dataset (WSDM Cup 2018) — real, 
anonymized data from KKBox, a major Asian music streaming service.

Why this matters: Getting a new customer costs 5-25x more than keeping an 
existing one. A tool that flags at-risk customers before they leave — and 
tells you why, and whether they're worth saving — turns a data science 
exercise into something with genuine dollar impact.

## 2. Problem Framing
- Type: Binary classification (is_churn: 1 = churned, 0 = retained)
- Churn definition: Provided directly by KKBox in train.csv — a customer is 
  churned if they do not renew a valid subscription within 30 days of their 
  membership expiring. Used as-is, not re-derived.
- Core challenge: Class imbalance (churners are the minority class), and 
  translating a probability into a business decision, not just a label.

## 3. Dataset
| File | Contents |
|---|---|
| train.csv | msno (customer ID) + is_churn label |
| members.csv | Demographics: city, age, gender, registration info |
| transactions.csv | Plan, payment method, price, renewal/cancellation flags, dates |
| user_logs.csv | Daily listening behavior — very large (multi-GB), must be read in chunks, never fully loaded into memory |

## 4. Who Is This Product For?
1. A recruiter/hiring manager skimming ~90 seconds — needs instant polish/relevance.
2. A technical reviewer digging deeper — needs ML rigor (metrics, explainability, engineering discipline).
Designed as if it's an internal tool a Retention/CS team would actually use.

## 5. Final Locked Feature Set
**A. Core Prediction & Explainability:** churn probability score, risk tiering 
(Low/Medium/High — thresholds TBD after seeing the real trained model's 
probability distribution), individual SHAP explanation per customer, global 
SHAP summary.

**B. Business Intelligence:** cohort/segment filters, top churn drivers by 
segment, CLV estimation, business impact/$ calculator (configurable), 
prioritized action list (ranked by expected value: probability × CLV − cost), 
suggested retention action (rule-based).

**C. UX:** customer search/lookup, historical usage trend chart, full 
slider-based what-if simulator.

**D. Engineering:** FastAPI backend with Swagger docs, Dockerized dev setup, 
CI pipeline (GitHub Actions), config-driven business logic, MLflow experiment 
tracking.

Deferred/parked: multi-model comparison, threshold-tuning tool, exportable 
reports, simulated alerts, time-to-churn survival estimate, data-drift 
monitoring.

Out of scope: true uplift modeling (no treatment/control data in KKBox), 
real-time streaming ingestion (dataset is static/historical).

## 6. End-to-End Architecture
Kaggle Raw Data → ETL + Feature Engineering (src/etl.py, src/features.py, 
chunked reads for user_logs.csv → customer_features.parquet) → Model Training 
(src/train.py: Logistic Regression baseline → XGBoost, StratifiedKFold, 
scale_pos_weight, MLflow logging) → Explainability (src/explain.py: 
shap.TreeExplainer, cached) → Business Impact Layer (src/business_impact.py: 
CLV, expected-value ranking, config/business_params.yaml) → FastAPI Backend 
(app/main.py) → Streamlit Frontend (app/Home.py + app/pages/) → Deployed 
(Backend → Render, Frontend → Streamlit Community Cloud).

Honesty note: "end-to-end" means data → model → API → UI → deployment, not a 
live production data pipeline. KKBox is static/historical.

## 7. Frontend Design
- Home/Cohort Dashboard: churn rate by segment, top global drivers, business 
  impact summary, filters.
- Customer Lookup: search by ID, churn probability + tier, SHAP waterfall, 
  CLV + $ impact, usage trend, suggested action.
- Model Performance: ROC, PR curve, confusion matrix, calibration plot.
- About: architecture diagram, tech stack, repo link, case-study summary.
Charts via Plotly; SHAP via streamlit-shap or embedded matplotlib.

## 8. Backend API Contract All request/response shapes defined with Pydantic (app/schemas.py).

## 9. Complete Tech Stack
See TECH_STACK_SPEC.md.

## 10. Repo Structure
See TECH_STACK_SPEC.md.

## 11. Project Roadmap (Full-Time Pace, ~3-3.5 weeks)
1. Data Understanding & EDA (Days 1-2)
2. Feature Engineering (Days 3-5)
3. Modeling (Days 6-8)
4. Explainability (Days 9-10)
5. Business Impact Layer (Days 10-11)
6. Backend API (Days 12-14)
7. Frontend (Days 15-17)
8. Containerization & CI (Days 18-19)
9. Deployment (Days 20-21)
10. Polish & Case Study (Days 22-23)

## 12. Master Concept Checklist
Class imbalance handling, proper cross-validation (StratifiedKFold), 
PR-AUC vs ROC-AUC, model calibration, SHAP explainability, CLV estimation, 
expected value decision framing, MLflow tracking, REST API design (Pydantic), 
decoupled frontend/backend, containerization, CI basics, config-driven logic.

## 13. Open Decisions / TODOs
- Risk tier thresholds — placeholders (0-0.3/0.3-0.6/0.6-1.0), finalize after 
  inspecting real predicted probability distribution.
- What-if simulator — full slider-based (DECIDED: full version).
- Final hosting choice — confirm within free-tier limits once model artifact 
  size and API latency are known.

This document should be updated as decisions evolve — treat it as living, not fixed.
