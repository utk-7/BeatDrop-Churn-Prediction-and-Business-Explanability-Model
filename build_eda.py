import nbformat as nbf

nb = nbf.v4.new_notebook()

# Section 1: Setup & data location check
nb.cells.append(nbf.v4.new_markdown_cell("""# Phase 1: Data Understanding & EDA
This notebook performs exploratory data analysis on the KKBox Churn Prediction dataset.
**Note on Data Versions:** Both v1 and v2 versions of `train` and `transactions` data were found in `data/raw/`. As per project conventions, we default to using the **v2** datasets, as they represent the most complete and updated snapshot provided by KKBox."""))

nb.cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import duckdb
import os
import py7zr

# Define all file paths
DATA_DIR = '../data/raw'
MEMBERS_PATH = os.path.join(DATA_DIR, 'members_v3.csv')
TRAIN_PATH = os.path.join(DATA_DIR, 'train_v2.csv')
TRANSACTIONS_PATH = os.path.join(DATA_DIR, 'transactions_v2.csv')
USER_LOGS_PATH = os.path.join(DATA_DIR, 'user_logs.csv')

# Verify required files exist
expected_files = [MEMBERS_PATH, TRAIN_PATH, TRANSACTIONS_PATH, USER_LOGS_PATH]
missing = [f for f in expected_files if not os.path.exists(f)]
if missing:
    raise FileNotFoundError(f"Missing required data files: {missing}. Please ensure data is present in data/raw/")
else:
    print("All required data files located successfully.")

# Helper to read 7z if needed, though pandas can read 7z natively if py7zr is installed
# e.g., pd.read_csv('file.7z')"""))

# Section 2: Load and inspect each table
nb.cells.append(nbf.v4.new_markdown_cell("## 2. Load and inspect tables\nLoading datasets and inspecting their shapes, datatypes, and initial rows. Printing memory usage."))
nb.cells.append(nbf.v4.new_code_cell("""# 1. Members
df_members = pd.read_csv(MEMBERS_PATH)
print("--- members_v3 ---")
print("Shape:", df_members.shape)
print("Memory Usage (MB):", df_members.memory_usage(deep=True).sum() / 1e6)
print(df_members.dtypes)
display(df_members.head())
display(df_members.describe())"""))

nb.cells.append(nbf.v4.new_code_cell("""# 2. Train (v2)
df_train = pd.read_csv(TRAIN_PATH)
print("\\n--- train_v2 ---")
print("Shape:", df_train.shape)
print("Memory Usage (MB):", df_train.memory_usage(deep=True).sum() / 1e6)
display(df_train.head())"""))

nb.cells.append(nbf.v4.new_code_cell("""# 3. Transactions (v2)
# File is ~50MB compressed, can be loaded into memory for EDA
df_trans = pd.read_csv(TRANSACTIONS_PATH)
print("\\n--- transactions_v2 ---")
print("Shape:", df_trans.shape)
print("Memory Usage (MB):", df_trans.memory_usage(deep=True).sum() / 1e6)
print(df_trans.dtypes)
display(df_trans.head())"""))

nb.cells.append(nbf.v4.new_markdown_cell("""### User Logs
We perform a small sample load (nrows=5000) for visual inspection, followed by a **size-agnostic aggregation using DuckDB** which will work seamlessly when the real 30GB+ file is used.
**Synthetic Data Notice**: `user_logs.csv` is currently a synthetic ~113k row sample representing ~8,000 customers. Findings below are illustrative of the generation script's logic."""))

nb.cells.append(nbf.v4.new_code_cell("""# 4a. User logs - Sample only load for inspection
df_logs_sample = pd.read_csv(USER_LOGS_PATH, nrows=5000)
print("--- user_logs (nrows=5000) ---")
display(df_logs_sample.head())"""))

nb.cells.append(nbf.v4.new_code_cell("""# 4b. User logs - Size-agnostic aggregation pass via DuckDB
# This SQL logic will scale to the 30GB+ file without running out of memory.
con = duckdb.connect()
query = f\"\"\"
SELECT 
    msno,
    COUNT(*) as total_log_days,
    SUM(num_25) as total_num_25,
    SUM(num_100) as total_num_100,
    AVG(total_secs) as avg_daily_secs
FROM read_csv_auto('{USER_LOGS_PATH}')
GROUP BY msno
LIMIT 5
\"\"\"
df_logs_agg = con.execute(query).df()
print("--- user_logs (DuckDB Aggregation) ---")
display(df_logs_agg)"""))

# Section 3: Churn label exploration & definition
nb.cells.append(nbf.v4.new_markdown_cell("""## 3. Churn label exploration & definition
Churn definition: A customer is considered churned (is_churn=1) if they do not renew within 30 days of their expiration date. We've documented the precise calculation mechanics in `CHURN_DEFINITION.md` based on `WSDMChurnLabeller.scala`."""))
nb.cells.append(nbf.v4.new_code_cell("""# Check distribution in train_v2
churn_dist = df_train['is_churn'].value_counts(normalize=True) * 100
print("Churn Distribution (%):\\n", churn_dist)"""))

# Section 4: Class balance
nb.cells.append(nbf.v4.new_markdown_cell("## 4. Class Balance\nUnderstanding the target imbalance ratio for modeling (scale_pos_weight)."))
nb.cells.append(nbf.v4.new_code_cell("""plt.figure(figsize=(6, 4))
sns.countplot(data=df_train, x='is_churn')
plt.title("Class Balance in train_v2")
plt.show()

ratio = df_train['is_churn'].value_counts()[0] / df_train['is_churn'].value_counts()[1]
print(f"Imbalance Ratio (Negative/Positive): {ratio:.2f}")"""))

# Section 5: Missingness analysis, per table
nb.cells.append(nbf.v4.new_markdown_cell("""## 5. Missingness Analysis

**Notes on User Logs**: Missingness in the synthetic user_logs reflects the generation script. Re-run this cell when real data is available.

| Table | Column | Null % | Notable Issue |
|---|---|---|---|
| members_v3 | gender | High | Gender is often not provided |
| members_v3 | bd | Low | Contains implausible ages (e.g. < 0, > 100) |
| transactions | various | Low/None | Check for duplicate daily transactions per msno |
"""))

nb.cells.append(nbf.v4.new_code_cell("""print("Members Null %:\\n", df_members.isnull().mean() * 100)
print("\\nTransactions Null %:\\n", df_trans.isnull().mean() * 100)

# Check for duplicate transactions (same msno, same transaction_date)
dupes = df_trans.duplicated(subset=['msno', 'transaction_date']).sum()
print(f"\\nDuplicate transaction rows (same msno, same date): {dupes}")"""))

# Section 6: Time range / temporal structure
nb.cells.append(nbf.v4.new_markdown_cell("## 6. Time Range / Temporal Structure"))
nb.cells.append(nbf.v4.new_code_cell("""print("Transactions: min date:", df_trans['transaction_date'].min(), "max date:", df_trans['transaction_date'].max())
print("Members: min expire date:", df_trans['membership_expire_date'].min(), "max expire date:", df_trans['membership_expire_date'].max())

# Plot record count over time to check right-censoring pattern
df_trans['trans_date_parsed'] = pd.to_datetime(df_trans['transaction_date'], format='%Y%m%d', errors='coerce')
df_trans.set_index('trans_date_parsed').resample('M').size().plot(title='Transactions over time')
plt.show()"""))

# Section 7: Cross-table consistency
nb.cells.append(nbf.v4.new_markdown_cell("## 7. Cross-table Consistency\nChecking how many users in `train_v2` have records in the other tables. Note: `user_logs` currently only covers ~8,000 customers due to the synthetic sample limit."))
nb.cells.append(nbf.v4.new_code_cell("""train_msno = set(df_train['msno'])
print(f"% in members: {len(train_msno.intersection(set(df_members['msno']))) / len(train_msno) * 100:.2f}%")
print(f"% in transactions: {len(train_msno.intersection(set(df_trans['msno']))) / len(train_msno) * 100:.2f}%")

# Query unique msno from user_logs via DuckDB
logs_msno_query = con.execute(f"SELECT DISTINCT msno FROM read_csv_auto('{USER_LOGS_PATH}')").df()['msno']
print(f"% in user_logs (synthetic 8k sample): {len(train_msno.intersection(set(logs_msno_query))) / len(train_msno) * 100:.2f}%")"""))

# Section 8: Light visual EDA
nb.cells.append(nbf.v4.new_markdown_cell("## 8. Light Visual EDA"))
nb.cells.append(nbf.v4.new_code_cell("""# Merge members and train for city EDA
df_eda = df_train.merge(df_members, on='msno', how='left')

plt.figure(figsize=(10, 4))
sns.barplot(data=df_eda, x='city', y='is_churn')
plt.title("Churn Rate by City")
plt.show()

# Average daily listening trend (synthetic data illustrative pattern)
query_trend = f\"\"\"
SELECT 
    t.is_churn,
    AVG(l.total_secs) as avg_secs
FROM read_csv_auto('{USER_LOGS_PATH}') l
JOIN read_csv_auto('{TRAIN_PATH}') t ON l.msno = t.msno
GROUP BY t.is_churn
\"\"\"
trend_df = con.execute(query_trend).df()
plt.figure(figsize=(6, 4))
sns.barplot(data=trend_df, x='is_churn', y='avg_secs')
plt.title("Synthetic Data — Illustrative Pattern: Avg Daily Listening (Churn vs Retained)")
plt.show()"""))

# Section 9: Data quality decisions log
nb.cells.append(nbf.v4.new_markdown_cell("""## 9. Data Quality Decisions Log
The findings from this notebook are summarized in `DATA_QUALITY_NOTES.md` at the project root, detailing missingness strategies, outlier handling (like implausible ages in `bd`), and synthetic data considerations for Phase 2 feature engineering."""))

with open('notebooks/01_eda.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Notebook generated at notebooks/01_eda.ipynb")
