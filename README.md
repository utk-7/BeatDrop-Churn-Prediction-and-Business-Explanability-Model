# BeatDrop Churn Prediction

A machine learning project for predicting churn and providing business explainability using KKBox data.

## Running Locally

There are two ways to run the BeatDrop platform locally:

### Option 1: Docker Compose (Recommended)
You can launch both the frontend and backend in containerized environments with a single command. 

```bash
docker-compose up -d
```
- The Dashboard will be available at [http://localhost:8080](http://localhost:8080)
- The Backend API will be available at [http://localhost:8000](http://localhost:8000)

*(Note: Containerization stability is verified automatically via the [GitHub Actions CI pipeline](.github/workflows/ci.yml) ensuring cross-platform compatibility, due to local machine Docker limitations during development.)*

### Option 2: Local Development (Python)
If you want to run the services natively for development:

1. **Start the backend**:
```bash
uvicorn app.main:app --port 8000 --reload
```

2. **Start the frontend**:
In a separate terminal, serve the `frontend/` directory:
```bash
cd frontend
python -m http.server 8080
```
- The Dashboard will be available at [http://localhost:8080](http://localhost:8080)

## Continuous Integration (CI) Testing Limitations

BeatDrop uses GitHub Actions for continuous integration. However, because the trained machine learning model (`models/xgboost_model_v0.2.0.joblib`, ~6.5MB) and the precomputed customer features dataset (`data/processed/customer_features.parquet`, ~47MB) are explicitly `.gitignore`d to prevent repository bloat, they are **not available** in the fresh CI environment.

As an intentional design decision, rather than creating brittle mock models that don't test true functionality, the CI pipeline is split:
- **What runs in CI:** Independent business logic, data transformation, and feature extraction tests (`test_business_impact.py`, `test_features.py`) use lightweight mock configurations and run successfully on every push.
- **What is skipped in CI:** API and Model inference tests (`test_api.py`, `test_model.py`) natively skip when the heavy `.joblib` or `.parquet` artifacts are missing. 

To run the full test suite, you must have the artifacts built locally (via `src/train.py`) and run `pytest` on your machine.
