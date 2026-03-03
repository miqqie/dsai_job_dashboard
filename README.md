# SG Job Market Intelligence Dashboard

## Summary

The **SG Job Market Trend Analysis Dashboard** turns over **1 million Singapore job postings** into actionable insights. It uses a **Polars + Parquet setup** with lazy execution (compute only when needed) and vectorized computation (operations on whole columns at once), providing sub-second responsiveness on large datasets.

Built for policy analysts and labor researchers, it answers questions like:

* Which Singapore industries pay the most?
* Are high-paying sectors struggling to hire?
* Which jobs are reposted frequently (potential talent shortage)?
* How does salary change by experience?

### Key Capabilities & Features

| Capability | Feature(s) | Why It Matters |
|------------|------------|----------------|
| High-Performance Analytics | Responsive UI | Built with **Polars** and optimized Streamlit components to handle large job datasets quickly—delivering fast, smooth dashboards. |
| Data Normalization & Aggregation | Filters & Drill-Downs | Transforms complex JSON data into structured, analysis-ready formats for accurate comparisons and easy sector deep dives. |
| Labor Market Monitoring | Interactive Visualizations | Tracks vacancies, salary trends, repost rates, and PMET vs Non-PMET shifts to quickly identify growth or shortages. |
| Policy Insights | Strategic Visualizations | Visual tools highlight competition, wage gaps, and demand-supply mismatches to support smarter workforce planning. |

🔗 Live Demo: [https://huggingface.co/spaces/Miqqie/job](https://huggingface.co/spaces/Miqqie/job)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Performance Engineering With Polars](#performance-engineering)
4. [Data Challenges](#data-challenges)
5. [Dashboard Capabilities](#dashboard-capabilities)
6. [Possible Future Enhancements](#future-enhancements)
7. [How to Run](#how-to-run)
8. [Project Highlights](#why-this-project-stands-out)

---

## 🚀 Project Overview <a id="project-overview"></a>

The dataset includes key job posting information such as job title, employment type and salary. It also captures employer name, posting dates, repost activity, application and view metrics. 

With over 1 million postings, the system’s main purpose is to measure and benchmark job sectors and understand broad labor market trends in a responsive manner.

To ensure fast, low-latency performance even at this scale, the system uses a 3-layer performance stack—columnar storage, zero-copy memory transfer, and lazy execution—eliminating sequential bottlenecks and enabling smooth, responsive analytics.

### 3 Key Features

⚡ **Sub-second Updates:** Filters or queries on 1M+ rows return results almost instantly.

📊 **Policy-Focused:** Breaks down data by sector, PMET/Non-PMET, and seniority.

🧠 **Mega-Request Engine:** Polars’ `pl.collect_all()` runs multiple calculations in parallel across CPU cores, avoiding repeated dataset scans.

[↑ Back to Table of Contents](#table-of-contents)

---

## 🏗 Architecture <a id="architecture"></a>

All chart requests are processed through a single optimized query pipeline, resolving analytics in parallel and updating the reactive UI efficiently.

### 🔁 Data Flow

**Parquet → Apache Arrow → Polars (Lazy Engine) → Pandas/NumPy → Streamlit + Plotly**

Each layer is isolated to prevent performance slowdowns.

### 🧱 3-Layer Performance Stack

| Layer            | Tools                       | Implementation                                                                                                                          | Outcome                                                   |
| ---------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Storage**      | Parquet + Arrow             | Parquet `stores columns separately`; Arrow allows `zero-copy memory sharing` (data can be accessed directly in memory without making additional copies).                                                               | Less I/O (fewer reads/writes to disk), lower memory usage, avoids duplicates           |
| **Compute**      | Polars + NumPy              | `Lazy execution` query runs all operations together. `pl.collect_all()` handles KPIs in parallel. NumPy vectorized ops speed computation. | Avoids repeated scans; fast processing on large datasets  |
| **Presentation** | Pandas + Streamlit + Plotly | Polars outputs go to Pandas for formatting. Streamlit manages state; Plotly renders interactive charts                                  | UI stays responsive without re-running heavy computations |

[↑ Back to Table of Contents](#table-of-contents)

---

## 📈 Performance Engineering With Polars <a id="performance-engineering"></a>

<img width="2752" height="1536" alt="unnamed (8)" src="https://github.com/user-attachments/assets/8a4da076-7562-4bbc-8473-bad473b0027e" />


<details>
<summary>📈 Benchmarking, Key Polar Techniques & Why Pandas Is Still Needed (Expand for more details)</summary>

<br> On an 8-core CPU + NVMe SSD, Polars + Parquet dramatically outperforms traditional Pandas + CSV:

| Phase           | Traditional (Pandas+CSV) | Optimized (Polars+Parquet)  | Advantage                            | Time Savings                  |
| --------------- | ------------------------ | --------------------------- | ------------------------------------ | ----------------------------- |
| Data Intake     | Loads all rows & columns | Reads only required columns | Loads only needed data               | 22.0s → 1.1s (95% faster)     |
| Computation     | Sequential               | Multicore                   | Parallel processing on all CPU cores | 8.5s → 0.9s (89% faster)      |
| Data Strategy   | Re-reads per chart       | Single "Mega-Request"       | One-time scan for all needed data    | 12.0s → 1.2s (90% faster)     |
| Aggregation     | Python loops             | Vectorized Rust ops         | Fast in-memory operations            | 4.0s → 1.2s (70% faster)      |
| Table Rendering | Relational merges        | Cached hash-map lookup      | Quick data lookup for tables         | 0.6s → 0.0005s (99.9% faster) |
| UI Interaction  | Full refresh each click  | Only relevant components    | Updates only changed parts           | 5.0s → <0.1s (98% faster)     |


### **Key Techniques:**

### 1. **Predicate Pushdown**

**Explanation**: Predicate pushdown refers to applying filters directly at the data loading stage (before it is fully loaded into memory). This reduces memory usage and speeds up the process by only reading the relevant data.

**Example**: In this example, we load a CSV file and apply a filter (predicate) to only read rows where the value of the `sector` column is "Technology", reducing the number of rows loaded into memory.

```python
import polars as pl

# Load data with a filter applied, using predicate pushdown
df = pl.scan_csv("job_data.csv", try_parse_dates=True).filter(pl.col("sector") == "Technology")

# Collect the filtered data
filtered_df = df.collect()

# Display the filtered DataFrame
print(filtered_df)
```

In this case, the filter `pl.col("sector") == "Technology"` is pushed down to the data source level, so only relevant rows are read.

---

### 2. **Categorical Casting**

**Explanation**: High-cardinality strings (e.g., "Technology", "Finance") can be inefficient for operations like grouping. Instead, we convert these columns into integers (categories), which improves performance for operations like grouping and aggregating.

**Example**: Convert the `sector` column (which is a high-cardinality string) into a categorical column, making it easier to perform grouping operations.

```python
import polars as pl

# Load the dataset
df = pl.read_csv("job_data.csv")

# Cast the 'sector' column to a categorical type
# Why: Polars converts each unique string into a small integer internally.
# This speeds up operations like groupby, join, and comparison because
# integer operations are faster than string operations and use less memory.
df = df.with_columns(pl.col("sector").cast(pl.Categorical))

# Perform a group-by operation using the categorical 'sector' column
# Aggregation now runs faster because Polars operates on integers instead of strings.
grouped_df = df.groupby("sector").agg([pl.col("vacancies").sum()])

# Display the result
print(grouped_df)
```

By casting `sector` to `Categorical`, Polars uses integer representations for the categories, speeding up operations like `groupby()`.

---

### 3. **Vectorized Cleaning**

**Explanation**: Vectorized operations are faster than using Python loops. Polars can use regular expressions (regex) to normalize or clean data in a single operation. This is especially useful for text-based cleaning tasks.

**Example**: Use regex to clean and normalize the `job_title` column, removing unwanted characters (e.g., extra spaces, punctuation).

```python
import polars as pl

# Load data
df = pl.read_csv("job_data.csv")

# Normalize job titles using regex (removes extra spaces and unwanted characters)
df = df.with_columns(
    pl.col("job_title").str.replace_all(r"\s+", " ").str.strip()
)

# Show the cleaned data
print(df)
```

In this example, the `str.replace_all()` method applies the regex pattern to the entire column to clean the `job_title` by normalizing spaces. This operation is vectorized, so it's fast.

---

### Summary:

1. **Predicate Pushdown**: Filters the data during loading to reduce memory usage.
2. **Categorical Casting**: Converts high-cardinality string columns into integers for faster grouping and aggregation.
3. **Vectorized Cleaning**: Uses regex for efficient and fast text cleaning operations across entire columns.

These optimizations can significantly improve both memory usage and performance when dealing with large datasets.

### Why Pandas Is Still Used: The Strategic Hybrid Architecture

Despite Polars’ dominance in high-scale computation, Pandas is intentionally retained as the **Final-Mile delivery layer**. This hybrid approach combines Rust-level computational speed with the mature presentation ecosystem of the Python data stack.

---

### 1. Efficiency Through "Data Thinning"

Pandas never interacts with the raw 1M+ row dataset. Instead, the architecture uses Polars to perform the "heavy lifting"—filtering, grouping, and aggregating—first. By the time data is converted to Pandas via `.to_pandas()`, it has been "thinned" from millions of records to a few dozen rows of summarized metrics.

* **Near-Zero Latency:** Because Pandas only processes a tiny fraction of the original data volume, UI updates remain instantaneous.
* **Lazy Execution Safety:** By keeping the data in a `LazyFrame` until the final `.collect()` call, the system ensures that user filters are "pushed down" to the storage layer. Pandas only ever receives the optimized result.

---

### 2. Technical Implementation: The Handoff

In `dashboardjob.py`, the transition occurs at the final moment of the computation cycle. This ensures that the Python Global Interpreter Lock (GIL) only affects the small visualization set, not the massive raw data.

```python
# 1. Computation (Heavy Lifting in Polars)
# Building the execution plan for 1M+ rows
kpi_task = lf_filtered.select([
    pl.col('numberOfVacancies').sum(),
    pl.col('average_salary').median()
])

# 2. The Handoff (The "Thinning" Moment)
# .collect() materializes the result; .to_pandas() wraps it for the UI
# df_res is now only a few rows, making this conversion instant.
kpi_res = kpi_task.collect().to_pandas()

# 3. Presentation (Pandas-Native UI)
st.metric(label="Total Vacancies", value=f"{kpi_res['numberOfVacancies'][0]:,.0f}")
```

---

### 3. Advanced UI Formatting & Visualization

While Polars is built for speed, the frontend ecosystem remains heavily Pandas-centric. Retaining Pandas allows the dashboard to utilize:

* **Streamlit `column_config`:** This API provides a high-level language for professional formatting (e.g., adding `S$` prefixes, `%` suffixes, and progress bars) that is natively optimized for Pandas objects.
* **Visualization Ecosystem:** Plotly and other charting libraries are natively designed to consume Pandas DataFrames. This handoff ensures full support for interactive features like synchronized tooltips and cross-filtering without compatibility hacks.
* **Apache Arrow Interoperability:** Because both libraries utilize the **Apache Arrow** memory standard, the `.to_pandas()` call is a high-throughput operation. It shares the existing memory buffer rather than performing a slow "copy-and-paste" of the data.

</details>

[↑ Back to Table of Contents](#table-of-contents)

---

## 🧱 Data Analysis & Processing Challenges <a id="data-challenges"></a>

### 1. Data Fragmentation (Nested JSON)

**Challenge:**
Critical attributes like industry tags are often embedded in complex JSON strings.

**Example:**
`[{"id":6,"category":"Building and Construction"},{"id":11,"category":"Engineering"}]`

**Solution:**
Regex-Driven Schema Normalization with Polars native expressions (`r'"category":\s*"([^"]+)"'`) isolates the industry label. Extraction occurs in the Parquet preprocessing phase, flattening JSON into a query-ready column before the user session.

```bash

lf = lf.with_columns(
    pl.col("categories")
    .cast(pl.Utf8)
    .str.replace_all("''", '"')
    .str.extract(r'"category":\s*"([^"]+)"', 1)
    .fill_null("General / Others")
    .alias("category")
)
```
**Technical Strategy:**
Polars-native regex captures the first industry label efficiently. Semantic similarity approaches (e.g., TF-IDF or `difflib`) added classification noise.

### 2. Job Title Normalization

**Challenge:**
Raw titles contain non-alphanumeric prefixes, inconsistent casing, and extra whitespace, fragmenting data.

**Solution:**
Hybrid Vectorized Cleaning & Cached Mapping: Vectorized regex cleaning standardizes titles. A Cached Title Map translates cleaned keys into polished, "Case-Smart" display names instantly.

``` bash
pl.col("title")
.str.replace_all(r"^[^a-zA-Z0-9]+", "")
.str.replace_all(r"\s+", " ")
.str.strip_chars()
```

**Technical Strategy:**
A chained `.str.replace_all()` and `.str.to_lowercase()` pipeline removes special characters and standardizes casing. Polished titles are assigned via an instant dictionary lookup to maintain UI responsiveness.

### 3. Hyper-Granularity vs. Usability

**Challenge:**
1M+ entries with granular job titles could obscure meaningful sector trends.

**Solution:**
**Broad Sector Mapping** consolidates sub-categories into **7 Broad Sectors** (e.g., Financial & Professional, Modern Services (ICT)). This preserves analytical depth while enabling clear macro-level trend detection.

``` bash
lf = lf.with_columns(
    pl.when(pl.col("category").str.to_lowercase() == "marketing / public relations")
    .then(pl.lit("Others"))
    .when(pl.col("category").str.to_lowercase().str.contains("finance|banking|legal|accounting|..."))
    .then(pl.lit("Financial & Professional"))
    .when(pl.col("category").str.to_lowercase().str.contains("software|programming|cyber|data|..."))
    .then(pl.lit("Modern Services (ICT)"))
    # ... additional mappings for Industrial, Consumer, and HR sectors
    .otherwise(pl.lit("Others"))
    .alias("broad_sector")
)
```

[↑ Back to Table of Contents](#table-of-contents)

---

## 📊 Dashboard Capabilities <a id="dashboard-capabilities"></a>

<img width="2752" height="1536" alt="unnamed (9)" src="https://github.com/user-attachments/assets/bd9a9448-62ce-4944-908d-61a1a969cd4d" />


<details>
<summary>📊 Dashboard Overview & Features (Expand for more details) </summary>

<br> The dashboard uses **sophisticated visualizations** to reveal hidden market forces and is structured progressively. Upper sections provide macro-level overviews, while lower sections drill into sector-specific and raw-level insights.

| Section | Key Visuals & Features | Metrics & Analytics |
|----------|-------------------------|---------------------|
| 1. Executive Pulse | Glass-morphism KPI Scorecards: Custom CSS metrics (stMetric) featuring blur effects, 16px border radius, and hover animations that shift cards upwards for a tactile, modern UI feel. | Parallel KPI Engine: Uses a single Polars "Mega-Collect" pass to simultaneously compute five metrics (Vacancies, Apps, Views, Posts, Reposts), reducing latency by ~4x compared to serial processing. |
| 2. Timeline Analysis | Dual-Axis Time Series: Stacked bars for vacancy volume vs. lines+markers for application density. Features x unified hovermode for instant cross-comparisons between PMET and Non-PMET trends. | On-the-Fly Granularity: Dynamically re-aggregates millions of rows across Weekly, Monthly, Quarterly, or Yearly buckets using Polars' high-speed group_by and dt.strftime methods. |
| 3. Market Map | Logarithmic Engagement Map: An interactive bubble chart using a log_x scale to handle high-variance vacancy data. Features high-visibility Red Borders (#FF0000) that highlight the top 3 most competitive sub-sectors. | Dynamic Quadrant Analysis: Automatically plots a "Weighted Avg Views" benchmark line. Overlays 4 context zones (Hotspot, Niche, Opportunity, Quiet Zone) to classify market activity. |
| 4. Career Structural Analysis | Hierarchical Sunburst: A 3-tier visual hierarchy (Sub-sector → Seniority → Data Ring). Slice sizes represent relative hiring volume to show structural distribution. | Market Positioning Benchmarks: Uses 📈/📉 icons generated by comparing sub-sector interquartile ranges (IQR) against broad sector benchmarks for both salary and experience. |
| 5. Friction-Premium Map | Strategic Quadrant Plot: A custom Plotly scatter plot mapping Salary Premium % (Y-axis) against Recruitment Friction (X-axis: % of Job Reposts). | Policy Logic & Insight: Identifies structural imbalances such as "Talent Scarcity" (High Pay + High Friction), "Retention Risk" (High Pay + Low Friction) to guide recruitment strategy. |
| 6. Detailed Sectoral Table | Interactive Streamlit Fragment: A performance-optimized UI component that handles "Final-Mile" delivery using the Streamlit column_config API for professional formatting (currency prefixes, progress bars). | "Title Map" Cache: Utilizes a dynamically calculated lookup dictionary to instantly display the most frequent job titles per sector without re-processing millions of strings during UI interaction. |

---

### Key Interactivity & Control Logic

The dashboard is designed for **Exploratory Data Analysis (EDA)**, allowing users to pivot from high-level market pulses to granular job-level insights without performance degradation.

---

## 1. Global Control Suite (The Sidebar)  
The sidebar acts as the primary "Command Center," utilizing Polars' Lazy Evaluation to update the engine’s query plan in a single pass.

- **Temporal Range Slider & Granularity:** A specialized date-range scroll bar. Users can also toggle between Weekly, Monthly, Quarterly, and Yearly granularities. Polars uses Predicate Pushdown to instantly exclude data points outside the selected window, ensuring calculations only occur on the relevant subset.

- **Categorical Deep-Dives (Sector & Seniority):** A unified filtering suite that updates the lf_filtered LazyFrame. This maps broad sectors to sub-sectors and includes a specific Seniority filter. Per the implementation logic, the workforce is bifurcated into PMET (Manager, Senior Manager, Executive, etc.) and Non-PMET (specifically targeting Non-Executive roles) to enable comparative structural analysis.

- **Repost Exclusion:** A specific control to filter out "Job Reposts" (metadata_repostCount > 0), allowing users to focus exclusively on unique, new vacancies.

## 2. Dynamic Visualization Interactivity  
- **Hierarchical Drill-Down (Sunburst):** Utilizes a Sub-Secotor → Position Level → Market Data Leaf hierarchy. Clicking a sub-sector drills into various seniority positions, where the outer "Leaf" ring visualizes specific salary benchmarks for various positions.

- **Intelligent Hover Tooltips:** Bubble charts feature calculated indicators. Using NumPy vectorization, tooltips display a 📈 / 📉 icon to show how a sector’s current applicant interest compares to the benchmark average.

- **Policy-Layer Annotations:** Both the Market Map and Friction-Premium Map include fixed quadrant labels (e.g., "The Hotspot," "Talent Scarcity," "Retention Risk") anchored via Paper Coordinates. This provides immediate strategic context regardless of data distribution, ensuring users can instantly classify sectors into zones of interest.

## 3. UI-Level Performance Optimizations  
- **The "Mega-Collect" Strategy:** To minimize latency, the dashboard creates a Unified Lazy Flow. Instead of multiple data reads, it executes KPIs, Timelines, and Chart data in a single parallel scan (pl.collect_all), maximizing CPU efficiency.

- **Targeted UI Updates (Streamlit Fragments):** The Detailed Sectoral Table is isolated via st.fragment. Users can filter or adjust table views without triggering a full-page rerun of the heavy Plotly charts, preserving scroll position and UI state.

- **Dynamic Title Aggregation & Parallel Execution:** Within the sectoral table, expensive string normalization is replaced by Dynamic Polars Projections. By removing static dictionary lookups in favor of a vectorized .str pipeline and Parallel Mega-Collections (pl.collect_all), the system calculates the "Most Frequent Titles" in real-time. This approach ensures accuracy across user-selected date ranges while processing over 1 million entries significantly faster than traditional methods.

</details>

[↑ Back to Table of Contents](#table-of-contents)

---

## 🔮 Possible Future Enhancements <a id="future-enhancements"></a>

#### **1. AI-based job title clustering (Sentence Transformers / BERTopic)**
  
- Convert raw job titles into semantic embeddings and cluster them to standardize inconsistent naming. This improves aggregation accuracy and workforce taxonomy clarity.

#### **2. Automated skills extraction via NER for skill-gap analysis**
  
- Use NER models to extract structured skills from job descriptions. This enables skill-demand tracking and quantitative skill-gap analysis.  

- **Note:** Named Entity Recognition (NER) is a natural language processing (NLP) technique that identifies and classifies key information (entities) in text into predefined categories.

#### **3. Labor shortage forecasting with Prophet or XGBoost**
  
- Apply time-series or machine learning models to predict hiring demand and recruitment friction. Supports proactive workforce planning.

#### **4. Cloud deployment with scheduled ETL pipelines**
  
- Automate data ingestion, transformation, and model updates in the cloud. Ensures scalable, production-ready analytics with regular refresh cycles.

[↑ Back to Table of Contents](#table-of-contents)

---

## ▶️ How to Run <a id="how-to-run"></a>

### Option 1: Local Environment Setup (Conda)

1. **Install the Requirements**

```bash
conda env create --file environment.yml
```

2. **Prepare the Data**
   Ensure `SGJobData.csv` is in the same directory. The system automatically builds `SGJobData_Cleaned.parquet` on first run.

> **Note:** CSV dataset is not included in the repo due to confidentiality. If you do not have access to the dataset, you can view the [live demo](https://huggingface.co/spaces/Miqqie/job) instead.

3. **Activate the Environment**

```bash
conda activate sg_job_market
```

4. **Start the Dashboard**

```bash
streamlit run dashboardjob.py
```

5. **Access the Interface**
   Local URL: `http://localhost:8501`
   If port `8501` is occupied, Streamlit uses `8502`, `8503`, etc. Check terminal output.

[↑ Back to Table of Contents](#table-of-contents)

---

### Option 2: Run via Docker (Recommended)

Using Docker to run your Streamlit dashboard is recommended because it packages your app, dependencies, system libraries, and runtime into a fully isolated container—ensuring consistent behavior across machines and deployment environments.

1. **Prerequisites**: Docker Desktop installed and running

2. **File Setup**: Ensure these files are in the project folder:

* `Dockerfile` – Instructions to build the Docker image (base image, dependencies, run command).
* `docker-compose.yml` – Defines and runs multi-container services with ports and settings.
* `requirements.txt` – Lists Python packages required for the **Streamlit** app.
* `.dockerignore` - Prevents unnecessary files from being copied into the Docker image, making builds faster and smaller.
* `SGJobData.csv`
  
> **Note:** The CSV dataset is not included in the repo due to confidentiality. If you do not have access to the dataset, you can view the [live demo](https://huggingface.co/spaces/Miqqie/job) instead.

3. **Launch the Dashboard**

**Windows (PowerShell):**

```powershell
docker-compose up -d; Start-Sleep -s 3; Start-Process "http://localhost:8501"
```

**Mac/Linux:**

```bash
docker-compose up -d && sleep 3 && open http://localhost:8501
```

**WSL/Ubuntu (inside Windows):**

```bash
docker-compose up -d && sleep 3 && powershell.exe start "http://localhost:8501"
```

4. **Management Commands**

| Action        | Command                        |
| ------------- | ------------------------------ |
| Stop & Remove | `docker-compose down`          |
| View Logs     | `docker-compose logs -f`       |
| Rebuild       | `docker-compose up -d --build` |
| Check Status  | `docker ps`                    |

[↑ Back to Table of Contents](#table-of-contents)

---

## 💡 Project Highlights <a id="why-this-project-stands-out"></a>

* Handles 1M+ rows with memory-mapped I/O
* Computation moved from UI to Rust-based Polars engine
* Clean separation of storage, compute, and presentation
* Bridges engineering analytics with policy insights
* Advanced charts support exploration and storytelling

[↑ Back to Table of Contents](#table-of-contents)

