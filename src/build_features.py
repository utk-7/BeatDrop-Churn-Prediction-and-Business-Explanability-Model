import os
import json
import pandas as pd
from datetime import datetime
import etl
import features

def main():
    print("Starting feature pipeline...")
    
    # Use the day before the test month starts for training features
    reference_date = '2017-02-28' 
    print(f"Using reference_date: {reference_date}")
    
    config = features.load_config()
    out_parquet = config['feature_pipeline']['output_parquet']
    out_metadata = config['feature_pipeline']['output_metadata']
    
    os.makedirs(os.path.dirname(out_parquet), exist_ok=True)
    
    print("Loading data...")
    members_df = etl.load_members()
    transactions_df = etl.load_transactions(reference_date=reference_date)
    logs_agg_df = etl.load_user_logs_agg(reference_date=reference_date)
    
    base_msno_df = etl.build_base_table(train_path="data/raw/train_v2.csv")
    print(f"Base cohort size: {len(base_msno_df)}")
    
    print("Building features...")
    customer_features = features.build_customer_feature_table(
        members_df, transactions_df, logs_agg_df, base_msno_df, reference_date
    )
    
    print("Merging target labels...")
    train_labels = pd.read_csv("data/raw/train_v2.csv")
    customer_features = pd.merge(customer_features, train_labels, on='msno', how='left')
    
    print(f"Final shape: {customer_features.shape}")
    
    print(f"Writing to {out_parquet}...")
    customer_features.to_parquet(out_parquet, index=False)
    
    print(f"Writing metadata to {out_metadata}...")
    metadata = {
        "pipeline_version": features.FEATURE_PIPELINE_VERSION,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "reference_date": reference_date,
        "user_logs_is_synthetic": True # per the project guidelines for phase 1/2
    }
    with open(out_metadata, "w") as f:
        json.dump(metadata, f, indent=2)
        
    print("Pipeline complete!")

if __name__ == "__main__":
    main()
