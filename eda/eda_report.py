import os
import re
import pandas as pd
import matplotlib.pyplot as plt


REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


# -----------------------------
# Helpers
# -----------------------------
def safe_series(df, col):
    """Return a safe cleaned string series for any column."""
    if col not in df.columns:
        return pd.Series(dtype="object")
    s = df[col].fillna("").astype(str).str.strip()
    s = s[s != ""]
    return s


def parse_price(price_text):
    """Extract numeric price from strings like '₹ 120 / Piece' or 'Rs 2000'."""
    if pd.isna(price_text):
        return None
    txt = str(price_text).replace(",", "")
    nums = re.findall(r"\d+\.?\d*", txt)
    return float(nums[0]) if nums else None


def save_barplot(series, title, filename, top_n=10):
    """Save bar plot for top categories/values."""
    if series is None or len(series) == 0:
        print(f"[EDA] Skipping plot: {title} (no data)")
        return

    top = series.value_counts().head(top_n)

    if len(top) == 0:
        print(f"[EDA] Skipping plot: {title} (empty after top_n)")
        return

    plt.figure(figsize=(10, 5))
    top.plot(kind="bar")
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(REPORT_DIR, filename))
    plt.close()


def normalize_location(loc):
    """Normalize locations like 'Chennai, Tamil Nadu' -> Tamil Nadu."""
    if not loc:
        return None
    loc = str(loc).strip()

    if "," in loc:
        parts = [p.strip() for p in loc.split(",") if p.strip()]
        return parts[-1] if parts else loc

    return loc


def iqr_outliers(series: pd.Series):
    """Return outliers using IQR method."""
    series = series.dropna()
    if len(series) < 5:
        return pd.Series([], dtype=float), None, None

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = series[(series < lower) | (series > upper)]
    return outliers, lower, upper


# -----------------------------
# Main EDA
# -----------------------------
def run_eda(cleaned_csv):
    if not cleaned_csv:
        print("[EDA] No cleaned CSV provided. Skipping EDA.")
        return

    df = pd.read_csv(cleaned_csv)

    print("\n===== EDA REPORT =====")
    print(f"Total records: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print("Columns:", list(df.columns))

    # -----------------------------
    # Category distribution
    # -----------------------------
    if "category" in df.columns:
        print("\n--- Category Counts ---")
        print(df["category"].value_counts())
        save_barplot(df["category"], "Category Distribution", "category_distribution.png", top_n=10)

    # -----------------------------
    # Missingness report
    # -----------------------------
    print("\n--- Missing Values (%) ---")
    missing_pct = (df.isna().mean() * 100).sort_values(ascending=False)
    print(missing_pct)

    # -----------------------------
    # Duplicate detection
    # -----------------------------
    print("\n--- Duplicate Detection ---")

    dup_cols = [c for c in ["category", "product_name", "product_url", "supplier", "location"] if c in df.columns]
    if len(dup_cols) >= 2:
        dup_mask = df.duplicated(subset=dup_cols, keep=False)
        dup_count = dup_mask.sum()
        print(f"Duplicate rows (based on {dup_cols}): {dup_count}")

        if dup_count > 0:
            dup_df = df[dup_mask].sort_values(dup_cols)
            dup_path = os.path.join(REPORT_DIR, "duplicates.csv")
            dup_df.to_csv(dup_path, index=False)
            print(f"✅ Saved duplicates list → {dup_path}")
        else:
            print("No duplicates found.")
    else:
        print("Not enough columns to check duplicates safely.")

    # -----------------------------
    # Supplier insights
    # -----------------------------
    supplier_s = safe_series(df, "supplier")
    print("\n--- Top Suppliers ---")
    if len(supplier_s) > 0:
        print(supplier_s.value_counts().head(10))
    else:
        print("No supplier data found.")
    save_barplot(supplier_s, "Top 10 Suppliers", "top_suppliers.png", top_n=10)

    # -----------------------------
    # Location insights
    # -----------------------------
    if "location" in df.columns:
        df["location_norm"] = df["location"].apply(normalize_location)
    loc_norm_s = safe_series(df, "location_norm")

    print("\n--- Top Locations (Normalized) ---")
    if len(loc_norm_s) > 0:
        print(loc_norm_s.value_counts().head(10))
    else:
        print("No location data found.")
    save_barplot(loc_norm_s, "Top 10 Locations (Normalized)", "top_locations.png", top_n=10)

    # -----------------------------
    # Price analysis + Outliers (IQR)
    # -----------------------------
    if "price" in df.columns:
        df["price_value"] = df["price"].apply(parse_price)

    print("\n--- Price Summary ---")
    if "price_value" in df.columns:
        price_vals = df.dropna(subset=["price_value"])
    else:
        price_vals = pd.DataFrame()

    if len(price_vals) > 5:
        print(price_vals["price_value"].describe())

        # Price distribution
        plt.figure(figsize=(8, 5))
        price_vals["price_value"].plot(kind="hist", bins=20)
        plt.title("Price Distribution")
        plt.tight_layout()
        plt.savefig(os.path.join(REPORT_DIR, "price_distribution.png"))
        plt.close()

        # Outlier detection (IQR)
        outliers, lower, upper = iqr_outliers(price_vals["price_value"])
        print("\n--- Outlier Detection (IQR) ---")
        print(f"Lower bound: {lower:.2f}, Upper bound: {upper:.2f}")
        print(f"Outlier count: {len(outliers)}")

        if len(outliers) > 0:
            outlier_rows = df[df["price_value"].isin(outliers)]
            out_path = os.path.join(REPORT_DIR, "price_outliers.csv")
            outlier_rows.to_csv(out_path, index=False)
            print(f"✅ Saved outlier rows → {out_path}")

        # Median price by category (if possible)
        if "category" in df.columns:
            price_by_cat = df.groupby("category")["price_value"].median().dropna().sort_values(ascending=False)
            if len(price_by_cat) > 0:
                plt.figure(figsize=(8, 5))
                price_by_cat.plot(kind="bar")
                plt.title("Median Price by Category")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                plt.savefig(os.path.join(REPORT_DIR, "median_price_by_category.png"))
                plt.close()

    else:
        print("Not enough price values for analysis/outliers.")

    # -----------------------------
    # Wordcloud
    # -----------------------------
    print("\n--- Wordcloud ---")
    try:
        from wordcloud import WordCloud

        if "product_name" in df.columns:
            text = " ".join(df["product_name"].fillna("").astype(str).tolist()).lower()
            # small cleanup
            text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) > 50:
                wc = WordCloud(width=1200, height=600, background_color="white").generate(text)

                plt.figure(figsize=(12, 6))
                plt.imshow(wc, interpolation="bilinear")
                plt.axis("off")
                plt.tight_layout()
                plt.savefig(os.path.join(REPORT_DIR, "wordcloud.png"))
                plt.close()

                print("✅ Saved wordcloud → reports/wordcloud.png")
            else:
                print("Not enough text to generate wordcloud.")
        else:
            print("product_name column missing, skipping wordcloud.")

    except Exception:
        print("Wordcloud not installed. To enable:")
        print("pip install wordcloud")

    # -----------------------------
    # Top suppliers per category heatmap
    # -----------------------------
    print("\n--- Suppliers per Category Heatmap ---")
    if "category" in df.columns and "supplier" in df.columns:
        tmp = df.copy()
        tmp["supplier"] = tmp["supplier"].fillna("").astype(str).str.strip()
        tmp = tmp[tmp["supplier"] != ""]

        if len(tmp) > 0:
            # Count suppliers per category
            supplier_counts = (
                tmp.groupby(["category", "supplier"])
                .size()
                .reset_index(name="count")
            )

            # Keep top 10 suppliers overall (to keep heatmap readable)
            top_suppliers = (
                supplier_counts.groupby("supplier")["count"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .index
                .tolist()
            )

            filtered = supplier_counts[supplier_counts["supplier"].isin(top_suppliers)]
            pivot = filtered.pivot_table(index="supplier", columns="category", values="count", fill_value=0)

            plt.figure(figsize=(10, 6))
            plt.imshow(pivot.values, aspect="auto")
            plt.title("Top Suppliers per Category (Counts)")
            plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45, ha="right")
            plt.yticks(range(len(pivot.index)), pivot.index)
            plt.tight_layout()
            plt.savefig(os.path.join(REPORT_DIR, "supplier_category_heatmap.png"))
            plt.close()

            # Save pivot table as CSV
            pivot_path = os.path.join(REPORT_DIR, "supplier_category_heatmap.csv")
            pivot.to_csv(pivot_path)
            print("✅ Saved heatmap + table:")
            print("   reports/supplier_category_heatmap.png")
            print("   reports/supplier_category_heatmap.csv")
        else:
            print("No supplier data available for heatmap.")
    else:
        print("category/supplier columns missing, skipping heatmap.")

    # -----------------------------
    # Summary text file for submission
    # -----------------------------
    summary_path = os.path.join(REPORT_DIR, "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("===== Slooze Take-Home Challenge EDA Summary =====\n\n")
        f.write(f"Total records: {len(df)}\n")
        f.write(f"Columns: {list(df.columns)}\n\n")

        if "category" in df.columns:
            f.write("Category counts:\n")
            f.write(df["category"].value_counts().to_string())
            f.write("\n\n")

        f.write("Missing values (%):\n")
        f.write(missing_pct.to_string())
        f.write("\n\n")

        if "price_value" in df.columns and len(price_vals) > 5:
            f.write("Price statistics:\n")
            f.write(price_vals["price_value"].describe().to_string())
            f.write("\n\n")

        # Mention duplicates
        if "dup_count" in locals():
            f.write(f"Duplicate rows found: {dup_count}\n\n")

    print(f"\n✅ Charts + summary saved in '{REPORT_DIR}/'")
    print(f"✅ Summary file: {summary_path}")
