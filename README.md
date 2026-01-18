# Slooze Data Engineering Challenge

## 📌 Overview
This project is a complete end-to-end data engineering solution designed to scrape, process, and analyze B2B marketplace data (specifically targeting **IndiaMART**). It demonstrates a robust pipeline suitable for extracting product information, simplifying it into a structured format, and deriving meaningful business insights.

The solution consists of three main modules:
1.  **Scraper (Part A)**: A hybrid crawler using **Playwright** (for dynamic listings) and **Requests/BeautifulSoup** (for high-speed detail enrichment).
2.  **ETL**: A cleaning pipeline to normalize data, extracting numeric prices and removing inconsistencies.
3.  **EDA (Part B)**: An automated explorative analysis engine that generates visualizations and statistical summaries.

---

## 🚀 Features

### Part A: Data Collection
-   **Hybrid Approach**: Uses `Playwright` to handle JavaScript-heavy listing pages and infinite scroll, while switching to `requests` for blazing fast product detail extraction.
-   **Robustness**: Includes delays, user-agent rotation, and error handling to respect target site limits.
-   **Scalability**: Configurable category list and page limits (`scraper/config.py`).
-   **Output**: Structured JSON files saved in `data/raw/`.

### Part B: Exploratory Data Analysis (EDA)
-   **Automated Reporting**: Generates a full suite of charts and a textual summary.
-   **Insights Generated**:
    -   **Price Analysis**: Distribution histograms, outlier detection using IQR.
    -   **Supplier Analysis**: Top suppliers and their category dominance (Heatmap).
    -   **Geographic Trends**: Normalized location analysis of suppliers.
    -   **Data Quality**: Duplicate detection and missing value reports.

---

## 🛠️ Installation

1.  **Clone/Download** the repository.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Install Playwright Browsers**:
    ```bash
    playwright install chromium
    ```

---

## 🏃 Usage

To run the entire pipeline (Scrape → ETL → EDA):

```bash
python main.py
```

### Configuration
You can modify `scraper/config.py` to:
-   Add more categories (`CATEGORIES` dict).
-   Increase crawl depth (`MAX_PAGES`).
-   Adjust delays (`REQUEST_DELAY`).

---

## 📂 Output Structure

After running, the project creates the following artifacts:

```text
├── data/
│   ├── raw/                  # Raw JSON files from scraper
│   └── processed/            # Cleaned CSV/JSON ready for analysis
├── reports/
│   ├── summary.txt           # Text summary of stats & insights
│   ├── price_distribution.png
│   ├── top_suppliers.png
│   ├── supplier_category_heatmap.png
│   ├── wordcloud.png         # Product keyword visualization
│   └── duplicates.csv        # Log of potential duplicate listings
```

---

## 📊 Sample Insights
(Based on generic runs)
-   **Price Parsing**: The generic currency format `₹` is parsed to floats for statistical analysis.
-   **Supplier Hubs**: Data often reveals regional hubs for specific industries (e.g., Gujarat/Maharashtra for industrial machinery).
-   **Market saturation**: The "Suppliers per Category" heatmap allows quick identification of niche vs. saturated markets.

---

## © License
This solution is submitted for the Slooze Data Engineering Challenge.
