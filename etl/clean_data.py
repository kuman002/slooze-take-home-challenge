import json
import pandas as pd
import re
import os

PROCESSED_DIR = "data/processed"

def extract_price_value(price_text):
    if not price_text:
        return None
    nums = re.findall(r"\d+\.?\d*", price_text.replace(",", ""))
    return float(nums[0]) if nums else None

def run_etl(raw_files):
    all_rows = []

    for file in raw_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_rows.extend(data)

    df = pd.DataFrame(all_rows)

    # Normalize columns
    df["product_name"] = df["product_name"].fillna("").str.strip()
    df["supplier"] = df["supplier"].fillna("").str.strip()
    df["location"] = df["location"].fillna("").str.strip()

    df["price_value"] = df["price"].apply(extract_price_value)

    # Drop empty product rows
    df = df[df["product_name"] != ""]

    # Save outputs
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    csv_path = f"{PROCESSED_DIR}/cleaned_products.csv"
    json_path = f"{PROCESSED_DIR}/cleaned_products.json"

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)

    print(f"[ETL] Saved cleaned CSV: {csv_path}")
    return csv_path
