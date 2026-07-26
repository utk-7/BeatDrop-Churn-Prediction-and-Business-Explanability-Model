# BeatDrop: Churn Prediction & Business Explanability Model

[Live Demo (Vercel)](https://beat-drop-churn-prediction-and-busi.vercel.app/) | [Backend API (Render)](https://beatdrop-api-2i3o.onrender.com/health)

> **Note on Cold Starts**: The backend is hosted on Render's free tier, which spins down after 15 minutes of inactivity. **Your first request may take up to 60 seconds** as the server wakes up. Thanks for your patience!

> **Current Known Issue**: The live Dashboard aggregation endpoints (`/cohort/stats` and `/business-impact/top-actions`) are currently failing on the Render deployment. This is an active memory constraint issue with Render's free tier, as calculating statistics across 971,000 precomputed predictions exceeds the 512MB RAM limit during startup. **Customer Lookup, the What-If Simulator, and Model Performance pages are unaffected and fully working.**

## The Problem
Acquiring a new customer is significantly more expensive than retaining an existing one. For subscription-based streaming platforms, failing to identify at-risk subscribers before they cancel directly impacts recurring revenue. We need a way to accurately predict churn risk, explain *why* a customer is at risk, and financially quantify the value of saving them.

## The Data
This project uses the [WSDM - KKBox's Churn Prediction Challenge](https://www.kaggle.com/c/kkbox-churn-prediction-challenge) dataset from 2018. It contains historical transaction logs, demographic data, and subscription details for nearly 1 million users. 
*(Honest Disclosure: Due to hardware constraints limiting the processing of the massive 1.5GB daily listening logs locally, a synthetic proxy for user logs was generated to demonstrate the engagement feature pipeline. This is documented in detail in `SYNTHETIC_DATA_NOTICE.md`. This represents a pragmatic engineering tradeoff to maintain pipeline integrity without being blocked by hardware).*

## The Approach
Our approach prioritized explainability and rigorous calibration over black-box accuracy.
1. **EDA & Feature Engineering**: We processed KKBox's disparate tables into a unified 33-feature customer profile, focusing on tenure, payment behavior, and demographics.
2. **Imbalance Handling**: Churn is a minority class. We utilized `scale_pos_weight` in XGBoost rather than SMOTE to maintain the true distribution of the data.
3. **Model & Calibration (The v0.1.0 to v0.2.0 Story)**: Our initial XGBoost model (v0.1.0) achieved strong separation but produced uncalibrated probabilities (drastically under-predicting true risk). In v0.2.0, we applied Isotonic Regression, correcting the calibration curve so that a predicted 60% churn probability genuinely translates to a 60% real-world churn rate.

## The Results
The calibrated v0.2.0 XGBoost model successfully identifies at-risk users without producing overconfident false alarms.
- **PR-AUC: 0.4134** (Precision-Recall Area Under Curve - highly robust for imbalanced data)
- **Brier Score: 0.0657** (Demonstrating strong probability calibration)

## Business Impact
Raw probabilities aren't actionable without financial context. This project includes a custom business logic layer that calculates:
- **Estimated Customer Lifetime Value (CLV)**: Based on the user's specific plan price.
- **Expected Value of Retention**: Prioritizes interventions not by raw churn risk, but by the financial ROI of saving that specific user, accounting for the discount cost and assumed success rate.

## Architecture

```mermaid
flowchart LR
    subgraph Data Pipeline
        A[KKBox Raw Data] --> B[ETL & Feature Eng]
    end
    
    subgraph Machine Learning
        B --> C[XGBoost Model]
        C --> D[Isotonic Calibration v0.2.0]
    end
    
    subgraph Backend API (Render)
        D --> E[FastAPI Server]
        E --> F[SHAP Explainer]
        E --> G[Business Impact Math]
    end
    
    subgraph Frontend (Vercel)
        H[Vanilla JS / HTML / CSS] <--> E
    end
```
*The architecture decouples the machine learning inference backend from a lightweight static frontend.*

## Live Demo
Despite the current dashboard limitation, there is plenty to explore in the [Live Demo](https://beat-drop-churn-prediction-and-busi.vercel.app/):
1. **Customer Lookup**: Search for any valid user (e.g., use the provided autocomplete), and view their individual SHAP waterfall chart explaining exactly which features drive their specific risk score.
2. **What-If Simulator**: Adjust a customer's tenure or payment plan in real-time and watch the live API recalculate their churn probability instantly.
3. **Model Performance**: View the actual calibration curves and global SHAP feature importance charts generated directly from the model metadata.

See `DEMO_WALKTHROUGH.md` for a guided tour.

## Limitations & Honest Disclosures
- **Synthetic Engagement Data**: As mentioned, the daily user listening logs were synthesized due to local hardware processing constraints.
- **Tenure Proxy Artifact**: During EDA, we discovered the `registered_via` feature acts as a proxy for customer tenure (certain registration methods were phased out over time). This makes it highly predictive of churn, but it is an artifact of the data collection window rather than a behavioral driver.
- **Memory Constraint Bug**: The `/cohort/stats` dashboard aggregation currently fails on Render because calculating group statistics across the 970K precomputed rows exceeds the 512MB RAM free-tier limit.

## How to Run Locally
Because of the Render memory constraints, the best way to experience the full, working Dashboard is locally via Docker.

```bash
# 1. Clone the repository
git clone https://github.com/utk-7/BeatDrop-Churn-Prediction-and-Business-Explanability-Model.git
cd BeatDrop-Churn-Prediction-and-Business-Explanability-Model

# 2. Run via Docker Compose
docker compose up --build

# 3. Access the services
# Frontend: http://localhost:8080
# Backend API: http://localhost:8000
```

## Tech Stack
| Layer | Technology |
|---|---|
| Language | Python 3.11, JavaScript (ES6) |
| Data Processing | pandas, numpy, pyarrow |
| Machine Learning | scikit-learn, XGBoost |
| Explainability | shap (TreeExplainer) |
| Backend API | FastAPI + Pydantic + Uvicorn |
| Frontend | Vanilla HTML, CSS, JS (No framework) |
| Containerization | Docker, Docker Compose |
| Hosting | Render (Backend), Vercel (Frontend) |
| CI/CD | GitHub Actions |
