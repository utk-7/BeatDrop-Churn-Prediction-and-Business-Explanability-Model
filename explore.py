import pandas as pd
# pyrefly: ignore [missing-import]
import duckdb
import os

print("--- MEMBERS ---")
members_path = "data/raw/members_v3.csv"
if os.path.exists(members_path):
    df_m = pd.read_csv(members_path)
    print("Shape:", df_m.shape)
    print("Nulls:\n", df_m.isnull().mean())
    print("Mins:\n", df_m.min(numeric_only=True))
    print("Maxs:\n", df_m.max(numeric_only=True))
    del df_m

print("\n--- TRANSACTIONS ---")
trans_path = "data/raw/transactions_v2.csv.7z"
# Let's check size instead since it's 7z, duckdb might not read 7z directly.
# Wait, let's use py7zr or just rely on train.csv/user_logs for now if we can't read 7z.
# Oh, pandas can't read 7z without py7zr. Let me check if py7zr is installed.
