# BeatDrop: Churn Prediction & Business Explanability Model

The best way to experience BeatDrop is to run it locally — this gives you the full, uninterrupted experience with no cold-start delays.

### Quick Start (Local Setup)
Ensure you have Docker Desktop installed, then run the following commands:
```bash
# 1. Clone the repository
git clone https://github.com/utk-7/BeatDrop-Churn-Prediction-and-Business-Explanability-Model.git
cd BeatDrop-Churn-Prediction-and-Business-Explanability-Model

# 2. Run via Docker Compose (Recommended)
docker compose up --build

# 3. Access the services
# Frontend: http://localhost:8080
# Backend API: http://localhost:8000
```
### Manual Setup (Without Docker)
If Docker Desktop is unavailable on your machine, you can run the services manually:
```bash
# 1. Start Backend (in terminal 1)
pip install -r requirements.txt
uvicorn app.main:app --port 8000

# 2. Start Frontend (in terminal 2)
cd frontend
python -m http.server 8080
```

*(Note: If you prefer to test the hosted version, please see the "Hosted Version" section below).*

---

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
    subgraph DataPipeline ["Data Pipeline"]
        A[KKBox Raw Data] --> B[ETL & Feature Eng]
    end
    
    subgraph MachineLearning ["Machine Learning"]
        B --> C[XGBoost Model]
        C --> D[Isotonic Calibration v0.2.0]
    end
    
    subgraph BackendAPI ["Backend API (Local/Render)"]
        D --> E[FastAPI Server]
        E --> F[SHAP Explainer]
        E --> G[Business Impact Math]
    end
    
    subgraph FrontendApp ["Frontend (Local/Vercel)"]
        H[Vanilla JS / HTML / CSS] <--> E
    end
```
*The architecture decouples the machine learning inference backend from a lightweight static frontend.*

## Hosted Version
A hosted version is also available at [beat-drop-churn-prediction-and-busi.vercel.app](https://beat-drop-churn-prediction-and-busi.vercel.app/).

The Dashboard's cohort-level view is still being finalized in the hosted environment due to an unresolved data-loading bug specific to the Render deployment, so the Customer Lookup, What-If Simulator, and Model Performance pages are the best parts to try there in the meantime. 
*(Note: As the backend is hosted on Render's free tier, your first request may take up to 60 seconds as the server wakes up).*

## Limitations & Honest Disclosures
- **Synthetic Engagement Data**: As mentioned, the daily user listening logs were synthesized due to local hardware processing constraints.
- **Tenure Proxy Artifact**: During EDA, we discovered the `registered_via` feature acts as a proxy for customer tenure (certain registration methods were phased out over time). This makes it highly predictive of churn, but it is an artifact of the data collection window rather than a behavioral driver.
- **Hosted Environment Data Bug**: The `/cohort/stats` dashboard aggregation currently fails on the Render deployment because of an unresolved environment-specific data loading issue that prevents the precomputed metrics from being fully loaded.

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
