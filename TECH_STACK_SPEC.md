# Tech Stack Specification — Beat Drop

| Layer | Tech |
|---|---|
| Language | Python 3.11 |
| Data wrangling | pandas, numpy, pyarrow (Parquet) |
| ML modeling | scikit-learn, XGBoost, Optuna |
| Imbalance handling | scale_pos_weight (primary), imbalanced-learn/SMOTE (fallback only) |
| Explainability | shap (TreeExplainer) |
| Experiment tracking | MLflow (local file store) |
| Backend API | FastAPI + Pydantic + Uvicorn |
| Frontend | Streamlit (multipage) + Plotly + streamlit-shap |
| API communication | requests (frontend → backend only) |
| Model serialization | joblib |
| Containerization | Docker (Dockerfile.api, Dockerfile.app, docker-compose.yml) |
| CI/CD | GitHub Actions |
| Testing | pytest (+ FastAPI TestClient) |
| Config management | YAML (config/business_params.yaml, config/thresholds.yaml) + python-dotenv |
| Hosting | Render (backend), Streamlit Community Cloud (frontend) |
| Version control | Git + GitHub |

## Repo Structure
```
kkbox-churn/
├── data/
│   ├── raw/                    # git-ignored
│   └── processed/              # git-ignored, customer_features.parquet
├── notebooks/                  # EDA + experimentation only
├── src/
│   ├── etl.py
│   ├── features.py
│   ├── train.py
│   ├── business_impact.py
│   └── explain.py
├── app/
│   ├── main.py                 # FastAPI app
│   ├── schemas.py               # Pydantic models
│   ├── Home.py                  # Streamlit entrypoint
│   └── pages/
│       ├── 1_Customer_Lookup.py
│       ├── 2_Model_Performance.py
│       └── 3_About.py
├── config/
│   ├── business_params.yaml
│   └── thresholds.yaml
├── models/                     # git-ignored: .joblib, shap cache
├── tests/
│   ├── test_features.py
│   ├── test_model.py
│   └── test_api.py
├── .github/workflows/ci.yml
├── Dockerfile.api
├── Dockerfile.app
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── TECH_STACK_SPEC.md
└── PROJECT_MASTER_GUIDE.md
```
