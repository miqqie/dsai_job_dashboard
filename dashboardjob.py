import os

import numpy as np
import pandas as pd  # noqa: F401
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import polars as pl
import streamlit as st
from plotly.subplots import make_subplots

pio.templates.default = "plotly_dark"

# Create a custom override to lock the background color
# Force all Plotly charts to use Inter
pio.templates["plotly_dark"].layout.paper_bgcolor = "#0e1117"
pio.templates["plotly_dark"].layout.plot_bgcolor = "#0e1117"
pio.templates["plotly_dark"].layout.font.family = "Inter"

# based on dashboard21.py
# 19
# added 2 columns % of total vac and app
# added st.expander to hide guides
# 20
# mobile resp
# 21
# changed default streamlit color from red to blue using config.toml

# Set page configuration
st.set_page_config(page_title="MOM Job Market Insights", layout="wide")

# 1. Main Title & CSS
st.markdown(
    """
    <h1 class="custom-header">
       <span class="gradient-text">SG Job Market Trend Analysis Dashboard</span>
    </h2>
    """,
    unsafe_allow_html=True,
)

# Detect if the screen is likely a mobile device based on sidebar state
is_mobile = st.query_params.get("view") == "mobile"
# Alternatively, use a simpler height variable:
chart_height = 400 if st.session_state.get("viewport_width", 1000) < 768 else 650

st.markdown(
    """
    <style>

    /* ================================
       1. TYPOGRAPHY & GLOBAL FONT
    ================================= */

    /* UNIFIED MODERN FONT (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"], .stMarkdown, p, div, span, label, table, td, th {
        font-family: 'Inter', sans-serif !important;
        color: #e2e8f0;
        letter-spacing: -0.01em;
    }


    /* ================================
       2. THEME LOCK (FORCED DARK MODE)
    ================================= */

    :root {
        --primary-color: #323cfc;
        --background-color: #0e1117;
        --secondary-background-color: #1a1c24;
        --text-color: #e2e8f0;
    }

    html, body, 
    [data-testid="stAppViewContainer"], 
    [data-testid="stHeader"] {
        background-color: #0e1117 !important;
        color: #e2e8f0 !important;
    }

    [data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }


    /* ================================
       3. LAYOUT STABILITY & SPACING
    ================================= */

    .main .block-container {
        overflow-x: hidden !important;
        padding-top: 4.5rem !important;
        background-color: #0e1117 !important;
    }

    .chart-container {
        width: 100% !important;
        overflow-x: hidden !important;
        display: block !important;
    }

    .stPlotlyChart {
        margin-bottom: 0px !important;
        width: 100% !important;
        max-width: 100% !important;
        margin-bottom: -45px !important; 
    }

    /* Pull the Sector Header down */
    .sector-header {
        margin-bottom: -25px !important;
        padding-bottom: 0px !important;
    }

    /* Additional spacing adjustment */
    .sector-header {
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    /* Target ONLY the Donut charts */
    div[data-testid="column"]:has(.sector-header) .stPlotlyChart {
        margin-top: -20px !important;
        padding-bottom: 60px !important;
    }

    /* Divider (Safety Rail) */
    hr {
        margin-top: 40px !important;
        margin-bottom: 20px !important;
        clear: both !important;
        display: block !important;
        border: none !important;
        border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    }


    /* ================================
       4. SIDEBAR & INPUTS
    ================================= */

    /* Sidebar Labels */
    [data-testid="stWidgetLabel"] p {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        margin-bottom: 8px !important;
    }

    /* Styled Selectboxes */
    div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 2px 4px !important;
        transition: all 0.3s ease !important;
    }

    div[data-baseweb="select"]:hover > div {
        border: 1px solid rgba(50, 60, 252, 0.4) !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
    }

    ul[role="listbox"] {
        background-color: #1a1c24 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }


    /* ================================
       5. EXPANDERS (GLASS + HOVER FIX)
    ================================= */

    /* Layout Stability */
    .stExpander details {
        transition: none !important;
    }

    .stExpander details[open] summary ~ * {
        animation: none !important;
    }

    /* Expander Container */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }

    div[data-testid="stExpander"]:hover {
        border-color: rgb(50, 60, 252) !important;
        transform: translateY(-4px);
    }

    div[data-testid="stExpander"] summary:hover span, 
    div[data-testid="stExpander"] summary:hover p,
    div[data-testid="stExpander"] summary:hover svg {
        color: white !important;
        fill: white !important;
    }

    /* Enhanced Expander */
    details[data-testid="stExpander"] {
        width: 100% !important;
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    details[data-testid="stExpander"]:hover {
        border: 1.5px solid rgba(50, 60, 252, 0.8) !important;
        transform: translateY(-6px) !important;
    }

    details[data-testid="stExpander"]:hover summary,
    details[data-testid="stExpander"]:hover summary p,
    details[data-testid="stExpander"]:hover summary svg {
        color: white !important;
        fill: white !important;
    }


    /* ================================
       6. KPI METRICS
    ================================= */

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 15px 20px !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-6px) !important;
        border: 1px solid rgba(50, 60, 252, 0.5) !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important; 
        font-weight: 600 !important;
        color: white !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: #94a3b8 !important;
    }


    /* ================================
       7. NOTIFICATIONS
    ================================= */

    div[data-testid="stNotification"] {
        background: rgba(50, 60, 252, 0.05) !important;
        border-left: 5px solid #323cfc !important; 
        border-radius: 12px !important;
    }


    /* ================================
       8. RESPONSIVE DESIGN
    ================================= */

    @media (min-width: 769px) {
        .stVerticalBlock { 
            gap: 0.5rem !important; 
        }
    }

    @media (max-width: 768px) {
        [data-testid="column"] { 
            margin-bottom: 30px !important; 
            width: 100% !important; 
        }

        .stPlotlyChart { 
            margin-bottom: -50px !important; 
        }

        h1 { 
            font-size: 1.5rem !important; 
        }
    }
  
    </style>
    """,
    unsafe_allow_html=True,
)
# Fixed Color Map
sector_colors = {
    "Financial & Professional": "#04412f",
    "Public Service, Education & Health": "#FADADD",
    "Modern Services (ICT)": "#323cfc",
    "Industrial & Infrastructure": "#149cae",
    "HR, General Administration and Management": "#e4efb9",
    "Consumer & Lifestyle": "#f59e0b",
    "Others": "#64748b",
}


@st.cache_resource
def get_cached_data():

    csv_path = "SGJobData.csv"
    processed_parquet_path = "SGJobData_Cleaned.parquet"

    # 1. MAINTENANCE: REBUILD LOGIC
    # This block remains identical to ensure your data cleaning pipeline stays intact
    if not os.path.exists(processed_parquet_path):
        if os.path.exists(csv_path):
            with st.spinner(
                "🚀 Rebuilding Optimized Parquet (Adding Period_Yearly)..."
            ):
                lf = pl.scan_csv(
                    csv_path, infer_schema_length=10000, ignore_errors=True
                )
                essential_cols = [
                    "metadata_jobPostId",
                    "title",
                    "postedCompany_name",
                    "employmentTypes",
                    "positionLevels",
                    "average_salary",
                    "salary_maximum",
                    "numberOfVacancies",
                    "minimumYearsExperience",
                    "metadata_totalNumberJobApplication",
                    "metadata_repostCount",
                    "metadata_totalNumberOfView",
                    "categories",
                    "metadata_newPostingDate",
                ]

                lf = (
                    lf.select(essential_cols)
                    .filter(
                        (pl.col("numberOfVacancies") < 10)
                        & (pl.col("salary_maximum") > 0)
                    )
                    .with_columns(
                        [
                            pl.col("metadata_newPostingDate")
                            .str.to_datetime(strict=False)
                            .alias("metadata_jobPostingDate"),
                            pl.col("title")
                            .str.replace_all(r"^[^a-zA-Z0-9]+", "")
                            .str.replace_all(r"\s+", " ")
                            .str.strip_chars(),
                            pl.when(pl.col("metadata_repostCount") > 0)
                            .then(pl.lit("Y"))
                            .otherwise(pl.lit("N"))
                            .alias("Job Repost"),
                            pl.when(
                                pl.col("positionLevels")
                                .cast(pl.Utf8)
                                .str.to_lowercase()
                                .str.contains("non-executive")
                            )
                            .then(pl.lit("Non-PMET"))
                            .otherwise(pl.lit("PMET"))
                            .alias("PMET"),
                        ]
                    )
                    .drop_nulls("metadata_jobPostingDate")
                )

                lf = lf.with_columns(
                    pl.col("categories")
                    .cast(pl.Utf8)
                    .str.replace_all("''", '"')
                    .str.extract(r'"category":\s*"([^"]+)"', 1)
                    .fill_null("General / Others")
                    .alias("category")
                )

                lf = lf.with_columns(
                    pl.when(
                        pl.col("category").str.to_lowercase()
                        == "marketing / public relations"
                    )
                    .then(pl.lit("Others"))
                    .when(
                        pl.col("category")
                        .str.to_lowercase()
                        .str.contains(
                            "finance|banking|legal|accounting|consult|insurance|audit|tax|risk|compliance|professional"
                        )
                    )
                    .then(pl.lit("Financial & Professional"))
                    .when(
                        pl.col("category")
                        .str.to_lowercase()
                        .str.contains(
                            "health|doctor|nurs|medical|educat|social|gov|public|community"
                        )
                    )
                    .then(pl.lit("Public Service, Education & Health"))
                    .when(
                        pl.col("category")
                        .str.to_lowercase()
                        .str.contains(
                            "software|programming|cyber|data|it |telecom|technology|digital|information tech"
                        )
                    )
                    .then(pl.lit("Modern Services (ICT)"))
                    .when(
                        pl.col("category")
                        .str.to_lowercase()
                        .str.contains(
                            "manufact|engin|logistics|construct|supply|energy|shipping|warehouse|architecture"
                        )
                    )
                    .then(pl.lit("Industrial & Infrastructure"))
                    .when(
                        pl.col("category")
                        .str.to_lowercase()
                        .str.contains(
                            "retail|hospitality|entertainment|beauty|f&b|food|travel|tourism|events|marketing|fashion"
                        )
                    )
                    .then(pl.lit("Consumer & Lifestyle"))
                    .when(
                        pl.col("category")
                        .str.to_lowercase()
                        .str.contains(
                            "general management|admin|administrative|human resources"
                        )
                    )
                    .then(pl.lit("HR, General Administration and Management"))
                    .otherwise(pl.lit("Others"))
                    .alias("broad_sector")
                )

                lf = lf.with_columns(
                    [
                        pl.when(
                            pl.col("positionLevels")
                            .cast(pl.Utf8)
                            .str.to_lowercase()
                            .str.contains("fresh/entry level|junior")
                        )
                        .then(pl.lit("Entry / Junior"))
                        .when(
                            pl.col("positionLevels")
                            .cast(pl.Utf8)
                            .str.to_lowercase()
                            .str.contains("senior management")
                        )
                        .then(pl.lit("Senior Management"))
                        .when(
                            pl.col("positionLevels")
                            .cast(pl.Utf8)
                            .str.to_lowercase()
                            .str.contains("middle management|manager|professional")
                        )
                        .then(pl.lit("Manager / Professional"))
                        .when(
                            pl.col("positionLevels")
                            .cast(pl.Utf8)
                            .str.to_lowercase()
                            .str.contains("non-executive")
                        )
                        .then(pl.lit("Others"))
                        .otherwise(pl.lit("Executive / Senior Executive"))
                        .alias("Position Level"),
                        pl.col("metadata_jobPostingDate")
                        .dt.year()
                        .cast(pl.Utf8)
                        .alias("Period_Yearly"),
                        (
                            pl.col("metadata_jobPostingDate").dt.year().cast(pl.Utf8)
                            + "-Q"
                            + pl.col("metadata_jobPostingDate")
                            .dt.quarter()
                            .cast(pl.Utf8)
                        ).alias("Period_Quarterly"),
                        pl.col("metadata_jobPostingDate")
                        .dt.strftime("%Y-%m")
                        .alias("Period_Monthly"),
                        (
                            pl.col("metadata_jobPostingDate").dt.year().cast(pl.Utf8)
                            + "-W"
                            + pl.col("metadata_jobPostingDate").dt.week().cast(pl.Utf8)
                        ).alias("Period_Weekly"),
                    ]
                )

                lf = lf.drop(
                    ["categories", "positionLevels", "metadata_newPostingDate"]
                )
                lf.collect().write_parquet(processed_parquet_path)
        else:
            st.error("Source CSV missing!")
            st.stop()

    # 2. UNIFIED PARALLEL LOADING (The Optimization)
    # Define required columns for projection
    required_cols = [
        "numberOfVacancies",
        "metadata_totalNumberJobApplication",
        "metadata_totalNumberOfView",
        "metadata_jobPostId",
        "metadata_repostCount",
        "average_salary",
        "broad_sector",
        "category",
        "Position Level",
        "PMET",
        "Job Repost",
        "title",
        "minimumYearsExperience",
        "Period_Weekly",
        "Period_Monthly",
        "Period_Quarterly",
        "Period_Yearly",
    ]

    # Initialize the scan
    lf = pl.scan_parquet(processed_parquet_path).select(required_cols)

    # Task A: Get Main Dataframe (with Categorical casting for speed)
    cat_cols = ["broad_sector", "category", "Position Level", "PMET", "Job Repost"]
    main_df_task = lf.with_columns([pl.col(c).cast(pl.Categorical) for c in cat_cols])

    # Task B: Extract unique metadata for UI widgets (Sectors, Levels, Categories)
    # We run these as lazy tasks so they execute in parallel with the main load
    subsector_task = lf.select("category").unique().sort("category")
    options_task = lf.select(["broad_sector", "Position Level", "PMET"]).unique()

    # NOTE: Title Task is REMOVED from here because it must now be calculated
    # dynamically based on the filtered date range in your main script.

    # 3. TRIGGER MEGA-COLLECT
    # Polars scans the file once and computes all results across all CPU cores
    df_res, sub_res, opt_res = pl.collect_all(
        [main_df_task, subsector_task, options_task]
    )

    # 4. POST-PROCESSING
    subsector_list = sub_res["category"].to_list()

    sector_mapping_df = (
        df_res.group_by("broad_sector")
        .agg(pl.col("category").unique().sort())
        .sort("broad_sector")
    )

    sector_map = {
        row["broad_sector"]: ", ".join(row["category"])
        for row in sector_mapping_df.to_dicts()
    }

    options = {
        "sectors": sorted(opt_res["broad_sector"].unique().to_list()),
        "levels": sorted(opt_res["Position Level"].unique().to_list()),
        "pmet": sorted(opt_res["PMET"].unique().to_list()),
        "sector_map": sector_map,  # Store it in the options dict
    }

    # Returning None for title_lookup_dict to signal it needs dynamic calculation
    return df_res, options, None, subsector_list


# INITIAL LOAD
df, options, title_lookup_dict, subsector_list = get_cached_data()


# 2. SIDEBAR WIDGETS
st.sidebar.header("🕹️ Control Panel")
granularity = st.sidebar.radio(
    "Select View Granularity",
    options=["Weekly", "Monthly", "Quarterly", "Yearly"],
    index=2,
)
period_col = f"Period_{granularity}"

sector_map = options.get("sector_map", {})
sorted_sector_names = sorted(sector_map.keys())
full_help_text = "**Broad Sector to Sub-sector Mapping:**\n\n" + "\n".join(
    [f"- **{s}**: {sector_map[s]}" for s in sorted_sector_names]
)

selected_sector = st.sidebar.selectbox(
    "Filter by Broad Sector",
    options=["All"] + options["sectors"],
    index=0,
    help=full_help_text,
)
selected_pmet = st.sidebar.selectbox(
    "Filter by PMET Status",
    options=["All"] + options["pmet"],
    help=(
        "**Classification Logic:**\n\n"
        "- **Non-PMET:** Only roles where position level is 'Non-executive'.\n"
        "- **PMET:** All other roles (Manager, Senior Executive, Entry/Junior, etc.)."
    ),
)
selected_pos_level = st.sidebar.selectbox(
    "Filter by Seniority", options=["All"] + options["levels"]
)
exclude_reposts = st.sidebar.checkbox("Exclude Job Reposts", value=False)

all_periods = sorted(df[period_col].unique().to_list())
selected_range = st.select_slider(
    f"Select {granularity} Range",
    options=all_periods,
    value=(all_periods[0], all_periods[-1]),
)


# 4. THE FRAGMENT
@st.fragment
def render_main_dashboard(date_range):
    # --- UNIFIED POLARS FILTERING (Replaces Pandas Mask) ---
    # Start with a LazyFrame to enable predicate pushdown
    lf_filtered = df.lazy()

    if selected_sector != "All":
        lf_filtered = lf_filtered.filter(pl.col("broad_sector") == selected_sector)
    if selected_pmet != "All":
        lf_filtered = lf_filtered.filter(pl.col("PMET") == selected_pmet)
    if selected_pos_level != "All":
        lf_filtered = lf_filtered.filter(pl.col("Position Level") == selected_pos_level)
    if exclude_reposts:
        lf_filtered = lf_filtered.filter(pl.col("Job Repost") == "N")
    lf_filtered = lf_filtered.filter(
        pl.col(period_col).is_between(pl.lit(date_range[0]), pl.lit(date_range[1]))
    )

    # --- 2. THE "MEGA-COLLECT" (Sub-6 Second Magic) ---
    # We define all summary needs first, then run them together
    kpi_task = lf_filtered.select(
        [
            pl.col("numberOfVacancies").sum().alias("vacs"),
            pl.col("metadata_totalNumberJobApplication").sum().alias("apps"),
            pl.col("metadata_totalNumberOfView").sum().alias("views"),
            pl.len().alias("posts"),
            pl.col("metadata_jobPostId")
            .filter(pl.col("Job Repost") == "Y")
            .count()
            .alias("reposts"),
        ]
    )
    timeline_task = (
        lf_filtered.group_by([period_col, "PMET"])
        .agg(
            [
                pl.col("numberOfVacancies").sum(),
                pl.col("metadata_totalNumberJobApplication").sum(),
            ]
        )
        .sort(period_col)
    )
    # Trigger ALL calculations in one single pass over the data
    # This is roughly 3-4x faster than multiple .collect() calls
    kpi_res, timeline_res = pl.collect_all([kpi_task, timeline_task])

    # Extract KPI values
    t_vac = kpi_res["vacs"][0] or 0
    t_apps = kpi_res["apps"][0] or 0
    t_views = kpi_res["views"][0] or 0
    t_posts = kpi_res["posts"][0] or 0
    t_reposts = kpi_res["reposts"][0] or 0

    # Display Metrics (Instantly)
    # Replace your current c1..c5 columns with this:
    # 1. Define the 5 columns for the metrics
    kpi_cols = st.columns(5)

    # 2. Prepare the data for the loop
    metrics = [
        ("Total Vacancies", f"{t_vac:,}"),
        ("Total Applications", f"{int(t_apps):,}"),
        ("Apps/Vac", f"{(t_apps / t_vac if t_vac > 0 else 0):.2f}"),
        ("Job Reposts", f"{int(t_reposts):,}"),
        ("Views/Post", f"{(t_views / t_posts if t_posts > 0 else 0):.1f}"),
    ]

    # 3. Loop through columns and metrics together
    for col, (label, value) in zip(kpi_cols, metrics):
        col.metric(label, value)
    # --- ROW 1: TIMELINE & DONUTS (UNIFIED POLARS FLOW) ---
    st.markdown("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown(
            f"""
    <h3 class="custom-header">
       <span class="gradient-text">Vacancies and Competition ({granularity})</span>
    </h3>
    """,
            unsafe_allow_html=True,
        )

        # st.subheader(f"Vacancies and Competition ({granularity})")

        # 1. POLARS AGGREGATION (REPLACES PANDAS GROUPBY)
        combo_data = (
            lf_filtered.group_by([period_col, "PMET"])
            .agg(
                [
                    pl.col("numberOfVacancies").sum(),
                    pl.col("metadata_totalNumberJobApplication").sum(),
                ]
            )
            .with_columns(
                (
                    pl.col("metadata_totalNumberJobApplication")
                    / pl.col("numberOfVacancies")
                )
                .fill_nan(0)
                .alias("Apps_per_Vacancy")
            )
            .sort(period_col)
            .collect()
            .to_pandas()
        )

        fig_combo = go.Figure()
        # Note: Column names in Polars agg default to original names unless aliased
        for status, color, label in [
            ("PMET", "#2c80d6", "PMET"),
            ("Non-PMET", "#f0e6c8", "Non-PMET"),
        ]:
            mask = combo_data["PMET"] == status
            fig_combo.add_trace(
                go.Bar(
                    x=combo_data[mask][period_col],
                    y=combo_data[mask]["numberOfVacancies"],
                    name=f"Vacancies ({label})",
                    marker_color=color,
                    offsetgroup=0,
                )
            )

        for status, color, label in [
            ("PMET", "#2b87e6", "PMET Line"),
            ("Non-PMET", "#f5f0e1", "Non-PMET Line"),
        ]:
            mask = combo_data["PMET"] == status
            # Round Apps_per_Vacancy to 2 decimal places
            y_values_2dp = combo_data[mask]["Apps_per_Vacancy"].round(2)
            fig_combo.add_trace(
                go.Scatter(
                    x=combo_data[mask][period_col],
                    y=y_values_2dp,
                    name=f"Apps/Vac ({label})",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(width=3, color=color),
                )
            )

        fig_combo.update_layout(
            dragmode=False,
            paper_bgcolor="#0e1117",  # Background of the entire chart area
            plot_bgcolor="#0e1117",  # Background of the actual plotting areatemplate="plotly_dark",
            barmode="stack",
            hovermode="x unified",
            height=650,
            legend_orientation="h",
            yaxis=dict(title="Number of Vacancies"),
            yaxis2=dict(
                title="Apps per Vacancy", overlaying="y", side="right", showgrid=False
            ),
            margin=dict(l=10, r=20, t=10, b=10),
        )

        for trace in fig_combo.data:
            if trace.type == "bar":  # only bar traces
                trace.marker.update(line_width=0, cornerradius=6)
        st.plotly_chart(fig_combo, use_container_width=True)

    with col_right:
        # 3. SENIORITY DONUT (POLARS)
        st.markdown(
            """
    <h3 class="custom-header">
       <span class="gradient-text">Applications by Seniority</span>
    </h3>
    """,
            unsafe_allow_html=True,
        )

        seniority_colors = {
            "Others": "#e0e0e0",  # very light grey
            "Entry / Junior": "#c2c2c2",  # light grey
            "Manager / Professional": "#9e9e9e",  # medium grey
            "Executive / Senior Executive": "#6e6e6e",  # dark grey
            "Senior Management": "#2f2f2f",  # very dark grey
        }

        donut_seniority_data = (
            lf_filtered.group_by("Position Level")
            .agg(pl.col("metadata_totalNumberJobApplication").sum())
            .collect()
            .to_pandas()
        )

        fig_donut1 = px.pie(
            donut_seniority_data,
            values="metadata_totalNumberJobApplication",
            names="Position Level",
            hole=0.6,
            color="Position Level",
            color_discrete_map=seniority_colors,
        )
        fig_donut1.update_layout(
            paper_bgcolor="#0e1117",  # Background of the entire chart area
            plot_bgcolor="#0e1117",  # Background of the actual plotting areatemplate="plotly_dark",
            showlegend=False,
            height=240,
            margin=dict(l=10, r=10, t=10, b=5),
        )
        st.plotly_chart(fig_donut1, use_container_width=True)

        # 2. SECTOR DONUT (POLARS)
        # Replace your st.markdown("### Applications by Sector") with this:

        st.markdown(
            """
    <h3 class="sector-header">
       <span class="gradient-text">Applications by Sector</span>
    </h3>
    """,
            unsafe_allow_html=True,
        )
        donut_sector_data = (
            lf_filtered.group_by("broad_sector")
            .agg(pl.col("metadata_totalNumberJobApplication").sum())
            .collect()
            .to_pandas()
        )

        fig_donut2 = px.pie(
            donut_sector_data,
            values="metadata_totalNumberJobApplication",
            names="broad_sector",
            hole=0.6,
            color="broad_sector",
            color_discrete_map=sector_colors,
        )
        fig_donut2.update_layout(
            paper_bgcolor="#0e1117",  # Background of the entire chart area
            plot_bgcolor="#0e1117",  # Background of the actual plotting area
            template="plotly_dark",
            showlegend=False,
            height=240,
            margin=dict(l=10, r=10, t=10, b=0),
        )

        st.plotly_chart(fig_donut2, use_container_width=True)

    # --- BUBBLE CHART ---
    st.markdown("---")
    st.markdown(
        """
    <h2 class="custom-header">
       <span class="gradient-text">1. Job Market Dynamics: Engagement vs. Job Supply</span>
    </h2>
    """,
        unsafe_allow_html=True,
    )

    with st.expander("💡 Market Dynamics Guide", expanded=False):
        st.info("""
        
        * **X-Axis (Market Supply — Vacancies):** Shows the number of open roles, with right indicating higher hiring activity and left indicating fewer opportunities.
        
        * **Y-Axis (Market Interest — Views per Posting):** Shows job seeker attention per role, with higher positions indicating stronger demand and lower positions indicating less interest.
        
        * **Bubble Size (Competition Volume):** The **larger the bubble, the higher the competition**. Size represents the ratio of applications to vacancies; a massive bubble suggests a crowded applicant pool.
        
        * **Color:** Distinguishes between different **broad parent sectors**.
        
        * **Red Borders:** Specifically highlight the **top 3 most competitive** categories (highest App/Vacancy ratio) regardless of their vacancy volume.
        
        * **Interactivity:** Hover over any bubble to see specific metrics for that sub-sector.
        """)
    bubble_data_lf = lf_filtered.group_by("category").agg(
        [
            pl.col("broad_sector").first(),
            pl.col("numberOfVacancies").sum(),
            pl.col("metadata_totalNumberJobApplication").sum(),
            pl.col("metadata_totalNumberOfView").sum(),
            pl.col("metadata_jobPostId").count(),
        ]
    )
    bubble_data = bubble_data_lf.collect().to_pandas()

    bubble_data["Views per Posting"] = (
        (bubble_data["metadata_totalNumberOfView"] / bubble_data["metadata_jobPostId"])
        .round(2)
        .fillna(0)
    )
    bubble_data["apps_per_vacancy"] = (
        (
            bubble_data["metadata_totalNumberJobApplication"]
            / bubble_data["numberOfVacancies"]
        )
        .round(2)
        .fillna(0)
    )
    # --- CALCULATING WEIGHTED AVERAGE (UNIFIED LAZY FLOW) ---
    # Instead of dividing two LazyFrames, we perform the math inside a .select()
    stats = lf_filtered.select(
        [
            (
                pl.col("metadata_totalNumberOfView").sum()
                / pl.col("metadata_jobPostId").count()
            ).alias("weighted_avg_views")
        ]
    ).collect()

    # Use .item() to extract the single resulting value
    weighted_avg_views = stats["weighted_avg_views"].item() or 0
    top_3_competitive = bubble_data.nlargest(3, "apps_per_vacancy")["category"].tolist()

    # 1. Create the base chart
    fig_bubble = px.scatter(
        bubble_data,
        x="numberOfVacancies",
        log_x=True,
        y="Views per Posting",
        size="apps_per_vacancy",
        color="broad_sector",
        color_discrete_map=sector_colors,
        hover_name="category",
        size_max=40,
        template="plotly_dark",
    )

    # 2. Apply red rings to bubbles in the chart and HIDE them from the legend
    for trace in fig_bubble.data:
        # Check if this is a bubble trace (avoiding hlines or empty traces)
        if hasattr(trace, "hovertext") and trace.hovertext is not None:
            # HIDE from legend so the red rings don't leak in
            trace.showlegend = False

            # Apply red rings for Top 3 categories
            trace.marker.line.color = [
                "#FF0000" if cat in top_3_competitive else "rgba(255,255,255,0.2)"
                for cat in trace.hovertext
            ]
            trace.marker.line.width = [
                3.5 if cat in top_3_competitive else 0.5 for cat in trace.hovertext
            ]
            trace.marker.opacity = 0.7

    # 3. ADD CLEAN HORIZONTAL LEGEND (Dummy Traces)
    # This creates a perfect horizontal legend with white borders only
    for sector in bubble_data["broad_sector"].unique():
        fig_bubble.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=sector,
                marker=dict(
                    size=12,
                    color=sector_colors.get(sector, "#FFFFFF"),
                    line=dict(color="rgba(255, 255, 255, 0.6)", width=1.5),
                ),
                showlegend=True,
            )
        )

    # 4. Quadrants & Formatting
    fig_bubble.update_xaxes(
        minor=dict(showgrid=False, ticks=""),
        dtick=1,
        title_text="Number of Vacancies (Log Scale)",
    )

    quadrants = [
        {
            "x": 0.95,
            "y": 1.1,
            "yanchor": "top",
            "text": "🔥 <b>The Hotspot</b><br>High Activity",
        },
        {
            "x": 0.05,
            "y": 1.1,
            "yanchor": "top",
            "text": "💎 <b>The Niche</b><br>High Interest, Low Supply",
        },
        {
            "x": 0.95,
            "y": -0.2,
            "yanchor": "bottom",
            "text": "⚡ <b>The Opportunity</b><br>High Supply, Low Interest",
        },
        {
            "x": 0.05,
            "y": -0.2,
            "yanchor": "bottom",
            "text": "💤 <b>The Quiet Zone</b><br>Low Activity",
        },
    ]

    for q in quadrants:
        fig_bubble.add_annotation(
            x=q["x"],
            y=q["y"],
            xref="paper",
            yref="paper",
            yanchor=q.get("yanchor", "middle"),
            text=q["text"],
            showarrow=False,
            font=dict(size=12, color="black", family="'Inter', sans-serif"),
            align="center",
            bgcolor="rgba(255, 255, 255, 0.8)",
            borderwidth=1,
            borderpad=5,
        )

    fig_bubble.add_hline(
        y=weighted_avg_views,
        line_dash="dot",
        line_color="#FFFFFF",
        annotation_text=f"Avg Views Per Posting: {weighted_avg_views:.1f}",
        annotation_position="top right",
    )

    # 5. FORCE HORIZONTAL LAYOUT (THE NUCLEAR FIX)
    fig_bubble.update_layout(
        dragmode=False,
        showlegend=True,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        height=700,  # Increased to give legend breathing room
        legend=dict(
            orientation="h",  # Horizontal
            entrywidth=220,  # Force a minimum width per item to keep them in line
            entrywidthmode="pixels",  # Ensures they don't stack vertically
            yanchor="top",
            y=-0.25,  # Move it well below the X-axis title
            xanchor="center",
            x=0.5,
            itemsizing="constant",
            font=dict(color="white", size=12),
            bgcolor="rgba(0,0,0,0)",
            traceorder="normal",
            tracegroupgap=0,  # Removes vertical gaps between traces
        ),
        # Crucial: Increase bottom margin to 200 to accommodate wrapping rows
        margin=dict(l=50, r=50, t=80, b=200),
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_bubble, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    # --- COMPETITION DEEP-DIVE ---

    # Change your existing header to this:
    # Replace your header with this:
    st.markdown("---")
    st.markdown(
        """
    <h2 class="custom-header">
       <span class="gradient-text">2. Competition Deep-Dive: Reward, Barrier & Market Structure</span>
    </h2>
    """,
        unsafe_allow_html=True,
    )

    with st.expander("💡 Competition Deep-Dive Guide", expanded=False):
        st.info("""
    
    **Layer 1: The Landscape (Bar Charts)**
    * **Rank:** Identifies the Top 10 sub-sectors by **Applications per Vacancy** (in brackets after subsector name).
    * It compares the **"Price of Entry"** (Avg. Experience Required) against the **"Financial Reward"** (Median Salary).
    * The darker the bars, the higher the pay/the longer the experience required

    **Layer 2: The Structure (Inner Sunburst - Top 5 Only)**
    * **Focus:** Deep-dive into the **Top 5** most competitive sub-sectors from Layer 1.
    * **Hierarchy:** Sub-sector (Center) → Seniority Level (Middle Ring).
    * **Volume:** Slice size indicates **Total Vacancies** (Hiring Volume).

    **Layer 3: The Data Ring (Outer Sunburst)**
    * **Pay IQR (Interquartile Range):** Shows the middle 50% (25th percentile – 75th percentile) to define "typical" market pay.
    * **Experience Benchmark:** Specific requirement vs. Broad Sector average.
    * **Positioning:** **📈/📉** icons signal if pay trends above or below sector norms.
    """)
    # --- 1. CONSOLIDATED DATA PREPARATION (Polars) ---

    # A. Broad Sector Benchmarks (Salary & Experience)
    broad_benchmarks_lazy = lf_filtered.group_by(
        ["broad_sector", "Position Level"]
    ).agg(
        [
            pl.col("average_salary").quantile(0.25).alias("broad_q1"),
            pl.col("average_salary").quantile(0.75).alias("broad_q3"),
            pl.col("minimumYearsExperience").mean().alias("broad_avg_exp"),
        ]
    )

    # --- B. Sub-sector Competition Stats (UNIFIED LAZY FLOW) ---
    subsector_stats_lf = (
        lf_filtered.group_by(["category", "broad_sector"])
        .agg(
            [
                pl.col("metadata_totalNumberJobApplication").sum().alias("apps"),
                pl.col("numberOfVacancies").sum().alias("vacs"),
                pl.col("average_salary").median().alias("median_salary"),
                pl.col("minimumYearsExperience").mean().alias("avg_exp"),
            ]
        )
        .with_columns(
            # 1. Calculate ratio with safety for division by zero
            (pl.col("apps") / pl.col("vacs").replace(0, None))
            .fill_nan(0)
            .fill_null(0)
            .alias("apps_per_vac")
        )
        .with_columns(
            # 2. Dynamic Y-axis label (Category + Ratio) calculated in Rust/C++ memory
            (
                pl.col("category").cast(pl.Utf8)
                + " ("
                + pl.col("apps_per_vac").round(1).cast(pl.Utf8)
                + ")"
            ).alias("category_with_ratio")
        )
    )
    subsector_stats_df = subsector_stats_lf.collect()

    # C. Identify Top 5 for Sunburst and Top 10 for Bars
    top_5_list = (
        subsector_stats_df.sort("apps_per_vac", descending=True)
        .head(5)["category"]
        .to_list()
    )

    # Prepare Pandas DF for Plotly (Sorting ascending for horizontal bar chart)
    top_10_comp = (
        subsector_stats_df.sort("apps_per_vac", descending=True)
        .head(10)
        .to_pandas()
        .sort_values("apps_per_vac", ascending=True)
    )

    # D. Detailed Stats for Sunburst
    sun_stats_df = (
        lf_filtered.filter(pl.col("category").is_in(top_5_list))
        .group_by(["category", "broad_sector", "Position Level"])
        .agg(
            [
                pl.col("average_salary").quantile(0.25).alias("q1"),
                pl.col("average_salary").quantile(0.75).alias("q3"),
                pl.col("minimumYearsExperience").mean().alias("avg_exp"),
                pl.col("numberOfVacancies").sum().alias("count"),
            ]
        )
        .join(broad_benchmarks_lazy, on=["broad_sector", "Position Level"], how="left")
        .collect()
        .to_pandas()
    )

    # --- 2. FINAL VECTORIZED LABELING (Consolidated) ---
    q1_s = sun_stats_df["q1"].fillna(0).astype(int).map("{:,}".format)
    q3_s = sun_stats_df["q3"].fillna(0).astype(int).map("{:,}".format)
    bq1_s = sun_stats_df["broad_q1"].fillna(0).astype(int).map("{:,}".format)
    bq3_s = sun_stats_df["broad_q3"].fillna(0).astype(int).map("{:,}".format)

    exp_s = sun_stats_df["avg_exp"].fillna(0).round(1).astype(str)
    b_exp_s = sun_stats_df["broad_avg_exp"].fillna(0).round(1).astype(str)

    sub_mid = (sun_stats_df["q1"] + sun_stats_df["q3"]) / 2
    broad_mid = (sun_stats_df["broad_q1"] + sun_stats_df["broad_q3"]) / 2
    perf_icon = np.where(sub_mid > broad_mid, "📈", "📉")

    sun_stats_df["Salary Comparison"] = (
        "<b>Sub-sector ("
        + sun_stats_df["Position Level"].astype(str)
        + "):</b><br>"
        + "Pay: $"
        + q1_s
        + "-$"
        + q3_s
        + " | Exp: "
        + exp_s
        + "y<br>"
        + "<b>Sector Benchmark:</b><br>"
        + "Pay: $"
        + bq1_s
        + "-$"
        + bq3_s
        + " | Exp: "
        + b_exp_s
        + "y<br>"
        + "("
        + perf_icon
        + " Market Positioning)"
    )

    # --- 3. RENDERING LAYOUT ---
    col_bars, col_sun = st.columns([1.1, 0.9])

    with col_bars:
        fig_deep = make_subplots(
            rows=1,
            cols=2,
            shared_yaxes=True,
            horizontal_spacing=0.18,
            subplot_titles=("Median Salary ($)", "Avg Exp Req (Yrs)"),
        )

        # Trace 1: Median Salary
        fig_deep.add_trace(
            go.Bar(
                y=top_10_comp["category_with_ratio"],
                x=top_10_comp["median_salary"],
                orientation="h",
                marker=dict(color=top_10_comp["median_salary"], colorscale="Purples"),
                text=top_10_comp["median_salary"].apply(lambda x: f"${x:,.0f}"),
                textposition="outside",
                cliponaxis=False,
            ),
            row=1,
            col=1,
        )

        # Trace 2: Average Experience
        fig_deep.add_trace(
            go.Bar(
                y=top_10_comp["category_with_ratio"],
                x=top_10_comp["avg_exp"],
                orientation="h",
                marker=dict(color=top_10_comp["avg_exp"], colorscale="Blues"),
                text=top_10_comp["avg_exp"].apply(lambda x: f"{x:.1f}y"),
                textposition="outside",
                cliponaxis=False,
            ),
            row=1,
            col=2,
        )

        # Disable interaction on the chart
        fig_deep.update_traces(hoverinfo="none", hovertemplate=None)

        fig_deep.update_layout(
            title={
                "text": "<b>Reward vs. Barrier (Top 10 Competitive)</b>",
                "y": 0.96,
                "x": 0.5,
                "xanchor": "center",
            },
            height=700,
            paper_bgcolor="#0e1117",  # Background of the entire chart area
            plot_bgcolor="#0e1117",  # Background of the actual plotting areatemplate="plotly_dark",
            showlegend=False,
            hovermode=False,  # This disables the hover globally for this figure
            margin=dict(l=250, r=20, t=120, b=40),
            dragmode=False,
        )
        # Adjusting X-axes for label space
        fig_deep.update_xaxes(
            range=[top_10_comp["median_salary"].max() * 1.4, 0], row=1, col=1
        )
        fig_deep.update_xaxes(
            range=[0, top_10_comp["avg_exp"].max() * 1.4], row=1, col=2
        )

        # CRITICAL MOVE: Place the chart rendering inside the column context
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(
                fig_deep, use_container_width=True, config={"displayModeBar": False}
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. OPTIMIZED SUNBURST WITH UNIFORM BRANCH COLORS ---
    with col_sun:
        # 1. PREPARE FORMATTED STRINGS & MARKET POSITIONING
        q1_s = (sun_stats_df["q1"] / 1000).apply(lambda x: f"{x:.1f}k")
        q3_s = (sun_stats_df["q3"] / 1000).apply(lambda x: f"{x:.1f}k")
        exp_s = sun_stats_df["avg_exp"].apply(lambda x: f"{x:.1f}")

        bq1_s = (sun_stats_df["broad_q1"] / 1000).apply(lambda x: f"{x:.1f}k")
        bq3_s = (sun_stats_df["broad_q3"] / 1000).apply(lambda x: f"{x:.1f}k")
        b_exp_s = sun_stats_df["broad_avg_exp"].apply(lambda x: f"{x:.1f}")

        # Logic for Market Positioning Icon
        sub_mid = (sun_stats_df["q1"] + sun_stats_df["q3"]) / 2
        broad_mid = (sun_stats_df["broad_q1"] + sun_stats_df["broad_q3"]) / 2
        perf_icon = np.where(sub_mid > broad_mid, "📈", "📉")

        # The Key Data String (Layer 3)
        sun_stats_df["Salary Comparison"] = (
            "<b>Sub-sector ("
            + sun_stats_df["Position Level"].astype(str)
            + "):</b><br>"
            + "Pay: $"
            + q1_s
            + "-$"
            + q3_s
            + " | Exp: "
            + exp_s
            + "y<br>"
            + "<b>Sector Benchmark:</b><br>"
            + "Pay: $"
            + bq1_s
            + "-$"
            + bq3_s
            + " | Exp: "
            + b_exp_s
            + "y<br>"
            + "("
            + perf_icon
            + " Market Positioning)"
        )

        # 2. COLOR MAPPING (Uniform branch colors)
        unique_cats = sun_stats_df["category"].unique()
        palette = px.colors.qualitative.Prism
        cat_color_map = {
            cat: palette[i % len(palette)] for i, cat in enumerate(unique_cats)
        }

        # 3. CONSTRUCT HIERARCHY
        ids, labels, parents, values, colors = [], [], [], [], []

        # Root Node
        ids.append("root")
        labels.append("<b>Top 5</b>")
        parents.append("")
        values.append(sun_stats_df["count"].sum())
        colors.append("#222")

        # Layer 1: Sub-sectors
        for cat in unique_cats:
            ids.append(cat)
            labels.append(f"<b>{cat}</b>")
            parents.append("root")
            values.append(sun_stats_df[sun_stats_df["category"] == cat]["count"].sum())
            colors.append(cat_color_map[cat])

        # Layer 2: Position Levels (Inherits parent color)
        for _, row in sun_stats_df.drop_duplicates(
            ["category", "Position Level"]
        ).iterrows():
            id_level = f"{row['category']}|{row['Position Level']}"
            ids.append(id_level)
            labels.append(row["Position Level"])
            parents.append(row["category"])
            values.append(
                sun_stats_df[
                    (sun_stats_df["category"] == row["category"])
                    & (sun_stats_df["Position Level"] == row["Position Level"])
                ]["count"].sum()
            )
            colors.append(cat_color_map[row["category"]])

        # Layer 3: Market Data Leaf (Inherits parent color)
        for _, row in sun_stats_df.iterrows():
            id_leaf = f"{row['category']}|{row['Position Level']}|data"
            ids.append(id_leaf)
            labels.append(row["Salary Comparison"])
            parents.append(f"{row['category']}|{row['Position Level']}")
            values.append(row["count"])
            colors.append(cat_color_map[row["category"]])

        # 4. SELECTIVE HOVER LOGIC
        hover_settings = []
        template_settings = []

        for current_id in ids:
            # If it's the root or a child/leaf (contains "|")
            if current_id == "root" or "|" in str(current_id):
                hover_settings.append("skip")
                template_settings.append("")  # Empty template prevents the ghost label
            else:
                # Only Layer 1 (Sub-sectors) remains active
                hover_settings.append("all")
                template_settings.append("<b>%{label}</b><extra></extra>")
        # 5. RENDER SUNBURST
        fig_sun = go.Figure(
            go.Sunburst(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                marker=dict(colors=colors),
                # Use the lists we just created
                hoverinfo=hover_settings,
                hovertemplate=template_settings,
            )
        )

        fig_sun.update_traces(
            insidetextorientation="horizontal",
            textfont=dict(size=14, color="white"),
            hoverlabel=dict(bgcolor="#222", font_size=16),
        )

        fig_sun.update_layout(
            # Move title down: 1.0 is the very top, 0.9 is slightly lower.
            # Use 'yref': 'paper' to position it relative to the chart area.
            title={
                "text": "Top 5 Competitive Sectors: Structural Drill-down",
                "y": 0.92,  # Shifting title downwards (from default 1.0)
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top",
            },
            height=800,
            margin=dict(t=10, b=0, l=10, r=10),
            paper_bgcolor="#0e1117",  # Background of the entire chart area
            plot_bgcolor="#0e1117",  # Background of the actual plotting areatemplate="plotly_dark",
            # Pull chart up: Decreasing top margin (t) shifts the chart area upwards
            # margin=dict(l=0, r=0, t=20, b=0),
            dragmode=False,
        )
        with st.container():
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(
                fig_sun, use_container_width=True, config={"displayModeBar": False}
            )
            st.markdown("</div>", unsafe_allow_html=True)
        # --- HELPER FOR TITLES ---

    def get_case_smart_titles(lf):
        """
        Corrected vectorized title processing.
        """
        # 1. Clean and normalize while Lazy
        lf_cleaned = lf.select(["category", "title"]).with_columns(
            [
                pl.col("title")
                .str.replace_all(r"^[^a-zA-Z0-9]+", "")
                .str.replace_all(r"\s+", " ")
                .str.strip_chars()
                .alias("cleaned_title"),
                pl.col("title").str.to_lowercase().alias("lower_title"),
            ]
        )

        # 2. Count specific casings
        case_counts = lf_cleaned.group_by(
            ["category", "cleaned_title", "lower_title"]
        ).agg(pl.len().alias("count"))

        # 3. Find dominant casing using window function
        dominant_casing = (
            case_counts.with_columns(
                pl.col("count")
                .max()
                .over(["category", "lower_title"])
                .alias("max_in_group")
            )
            .filter(pl.col("count") == pl.col("max_in_group"))
            .unique(subset=["category", "lower_title"])
        )

        # 4. Rank and Implode into List before joining
        top_titles = (
            dominant_casing.sort("count", descending=True)
            .group_by("category")
            .head(3)
            .group_by("category")
            .agg(
                pl.col("cleaned_title")
                .implode()
                .list.join(", ")
                .alias("Most Frequent Titles")
            )
        )

        # --- CRITICAL FIX: RETURN THE DATAFRAME ---
        return top_titles.collect().to_pandas()

    # --- MARKET FRICTION SECTION ---
    st.markdown("---")
    st.markdown(
        """
    <h2 class="custom-header">
       <span class="gradient-text">3. High-Volume Magnetism: Vacancy Clusters, Listing Friction & Reward Premiums</span>
    </h2>
    """,
        unsafe_allow_html=True,
    )

    with st.expander("💡 Friction-Premium Map Guide", expanded=False):
        st.info("""
   
    * **X-Axis (Salary Premium %):** Comparison against the **Median** salary of the parent broad sector.
    * **Y-Axis (Friction %):** % of repostings (Higher = Harder to fill).
    * **Bubble Size:** Competition level (Applications per Vacancy). The larger the bubble, the more competitive the sub-sector.
    * **Color:** Represents the median salary (darker = higher pay).
    * **Interactivity:** Hover over any bubble to see specific metrics for that sub-sector.
    """)
    # 1. DEFINE BENCHMARKS FIRST
    # This calculates the median salary for each broad sector across the filtered timeframe
    benchmarks_lf = lf_filtered.group_by("broad_sector").agg(
        pl.col("average_salary").median().alias("broad_sector_median")
    )
    # 2. AGGREGATE SUB-SECTOR DATA (LAZY)
    market_friction_df = (
        lf_filtered.group_by(["category", "broad_sector"])
        .agg(
            [
                pl.col("metadata_jobPostId").count().alias("postings"),
                pl.col("numberOfVacancies").sum().alias("vacancies"),
                pl.col("metadata_totalNumberJobApplication").sum().alias("apps"),
                pl.col("average_salary").median().alias("median_salary"),
                # Calculate raw repost count
                (pl.col("Job Repost") == "Y").sum().alias("repost_count"),
            ]
        )
        # Join with benchmarks for Salary Premium calculation
        .join(benchmarks_lf, on="broad_sector")
        .with_columns(
            [
                # Salary Premium %
                (((pl.col("median_salary") / pl.col("broad_sector_median")) - 1) * 100)
                .round(2)
                .alias("salary_premium_pct"),
                # Friction % (REPOST PERCENTAGE)
                ((pl.col("repost_count") / pl.col("postings")) * 100)
                .round(2)
                .alias("friction_pct"),
                # Competition: Apps per Vacancy
                (pl.col("apps") / pl.col("vacancies").replace(0, None))
                .fill_nan(0)
                .round(2)
                .alias("apps_per_vac"),
            ]
        )
        .sort("vacancies", descending=True)
        .head(10)
        .collect()
        .to_pandas()
    )

    # --- 2. BUBBLE CHART VISUALIZATION ---
    fig_premium = px.scatter(
        market_friction_df,
        x="salary_premium_pct",
        y="friction_pct",  # FIX: Changed from 'reposts' to 'friction_pct'
        size="apps_per_vac",
        color="median_salary",
        hover_name="category",
        text="category",
        labels={
            "salary_premium_pct": "Salary Premium vs. Sector Median (%)",
            "friction_pct": "Market Friction (% Reposted)",  # Updated Label
            "apps_per_vac": "Apps per Vacancy",
            "median_salary": "Median Salary ($)",
        },
        size_max=50,
        color_continuous_scale="Purples",
        template="plotly_dark",
        title="<b>The Friction-Premium Map (Top 10 High-Volume Sectors)</b>",
    )

    # --- 3. STYLING & QUADRANTS ---
    # Use the calculated friction percentage median for the horizontal line
    friction_median = market_friction_df["friction_pct"].median()

    fig_premium.add_vline(x=0, line_dash="dash", line_color="gray")
    fig_premium.add_hline(y=friction_median, line_dash="dash", line_color="gray")

    fig_premium.update_traces(
        textposition="top center",
        marker=dict(opacity=0.85, line=dict(width=1, color="white")),
    )

    fig_premium.update_layout(
        dragmode=False,
        height=650,
        paper_bgcolor="#0e1117",  # Background of the entire chart area
        plot_bgcolor="#0e1117",  # Background of the actual plotting area
        xaxis=dict(
            title="Salary Premium (%) vs. Parent Sector Median",
            showgrid=True,
            zeroline=False,
            ticksuffix="%",
            automargin=True,  # Ensures labels don't get cut off when margins are small
        ),
        yaxis=dict(title="Recruitment Friction (% Reposted)", ticksuffix="%"),
        margin=dict(l=20, r=20, t=80, b=150),
        coloraxis_colorbar=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,  # Adjust this value if it overlaps with X-axis labels
            xanchor="center",
            x=0.5,
            title=dict(text="Median Salary ($)", side="top"),
            thickness=15,
            len=0.4,  # Length of the bar (e.g. 0.5 = 50% of chart width)
        ),
    )
    # --- UPDATED QUADRANT LABELS ---
    quadrant_annotations = [
        # Top Right: High Premium + High Repost (Hard to find + Expensive)
        dict(
            x=1.0,
            y=1.05,
            xref="paper",
            yref="paper",
            text="<b>TALENT SCARCITY</b><br>High Pay & High Friction<br><i>(Specialized / Talent Shortage)</i>",
            showarrow=False,
            xanchor="right",
            yanchor="top",
            font=dict(color="black", size=11, family="'Inter', sans-serif"),
            bgcolor="rgba(255, 230, 230, 0.85)",  # Light Red/Pink alert
            bordercolor="rgba(150, 0, 0, 0.5)",
            borderwidth=1,
            borderpad=8,
        ),
        # Top Left: Low Premium + High Repost (Low pay + Hard to fill)
        dict(
            x=-0,
            y=1.05,
            xref="paper",
            yref="paper",
            text="<b>RETENTION RISK</b><br>Low Pay & High Friction<br><i>(Struggling to Attract/Retain)</i>",
            showarrow=False,
            xanchor="left",
            yanchor="top",
            font=dict(color="black", size=11, family="'Inter', sans-serif"),
            bgcolor="rgba(255, 243, 205, 0.85)",  # Amber warning
            bordercolor="rgba(133, 100, 4, 0.5)",
            borderwidth=1,
            borderpad=8,
        ),
        # Bottom Right: High Premium + Low Repost (High pay + Easy fill)
        dict(
            x=1,
            y=-0.2,
            xref="paper",
            yref="paper",
            text="<b>PREMIUM STABILITY</b><br>High Pay & Low Friction<br><i>(Attractive / Expanding)</i>",
            showarrow=False,
            xanchor="right",
            yanchor="bottom",
            font=dict(color="black", size=11, family="'Inter', sans-serif"),
            bgcolor="rgba(212, 237, 218, 0.85)",  # Green health
            bordercolor="rgba(40, 167, 69, 0.5)",
            borderwidth=1,
            borderpad=8,
        ),
        # Bottom Left: Low Premium + Low Repost (Low barrier/pay + Easy fill)
        dict(
            x=-0,
            y=-0.2,
            xref="paper",
            yref="paper",
            text="<b>HIGH-FLUIDITY ROLES</b><br>Low Pay & Low Friction<br><i>(High Supply / Entry Level)</i>",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(color="black", size=11, family="'Inter', sans-serif"),
            bgcolor="rgba(224, 240, 255, 0.85)",  # Blue neutral
            bordercolor="rgba(0, 123, 255, 0.5)",
            borderwidth=1,
            borderpad=8,
        ),
    ]
    with st.container():
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        fig_premium.update_layout(annotations=quadrant_annotations)
        st.plotly_chart(fig_premium, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- UPDATED SECTORAL SUMMARY TABLE WITH BLUE SELECTION BOXES ---

    # --- UPDATED SECTORAL SUMMARY TABLE WITH TOP 10 OPTIONS ---

    # This recalculates based on your slider/sidebar filters
    dynamic_title_df = (
        lf_filtered.select(["category", "title"])
        .with_columns([pl.col("title").str.to_lowercase().alias("lower_title")])
        .group_by(["category", "title", "lower_title"])
        .agg(pl.len().alias("count"))
        .with_columns(
            pl.col("count")
            .max()
            .over(["category", "lower_title"])
            .alias("max_in_group")
        )
        .filter(pl.col("count") == pl.col("max_in_group"))
        .unique(subset=["category", "lower_title"])
        .sort("count", descending=True)
        .group_by("category")
        .head(3)
        .group_by("category")
        .agg(pl.col("title").implode().list.join(", ").alias("titles"))
        .collect()
    )

    dynamic_title_lookup = dict(
        zip(dynamic_title_df["category"], dynamic_title_df["titles"])
    )

    @st.fragment
    def render_summary_section(lf_in, title_lookup_dict, sub_list):
        st.markdown(
            """<style>span[data-baseweb="tag"] { background-color: #1f77b4 !important; }</style>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
    <h2 class="custom-header">
       <span class="gradient-text">4. Detailed Sectoral Table</span>
    </h2>
    """,
            unsafe_allow_html=True,
        )

        # --- 0. PRE-CALCULATE STABLE MARKET TOTALS ---
        # Calculate from the full filtered dataset (sidebar scope) to ensure
        # percentages are consistent even when "Top 10" or sub-sector filters are applied.
        market_totals = lf_in.select(
            [
                pl.col("numberOfVacancies").sum().alias("total_v"),
                pl.col("metadata_totalNumberJobApplication").sum().alias("total_a"),
            ]
        ).collect()

        total_mkt_vacancies = (
            market_totals["total_v"][0]
            if market_totals["total_v"][0] and market_totals["total_v"][0] != 0
            else 1
        )
        total_mkt_apps = (
            market_totals["total_a"][0]
            if market_totals["total_a"][0] and market_totals["total_a"][0] != 0
            else 1
        )

        # --- SETUP FILTERING WIDGETS ---
        special_options = [
            "Top 10 Most Competitive Sub Sectors",
            "Top 10 Sub Sectors with Highest Vacancies",
        ]

        selected_sub = st.multiselect(
            "🔍 Filter by Sub-sectors. Rows are colour coded by broad sectors:",
            options=["All"] + special_options + sub_list,
            default="All",
            key="summary_sector_filter",
        )

        if not selected_sub:
            st.warning("Please select at least one sub-sector.")
            return

        # --- 1. DYNAMIC BENCHMARK CALCULATIONS ---
        sector_benchmarks = lf_in.group_by("broad_sector").agg(
            [
                pl.col("average_salary").median().alias("Parent Sector Median"),
                pl.col("minimumYearsExperience").mean().alias("Parent Sector Avg Exp"),
            ]
        )

        # --- 2. SENIORITY METRIC (POPULAR LEVEL) ---
        top_apps_seniority = (
            lf_in.group_by(["category", "Position Level"])
            .agg(pl.col("metadata_totalNumberJobApplication").sum().alias("s_apps"))
            .sort("s_apps", descending=True)
            .group_by("category")
            .head(1)
            .select(
                ["category", pl.col("Position Level").alias("Top Seniority (Apps)")]
            )
        )

        # --- 3. MAIN AGGREGATION PIPELINE ---
        summary_lf = lf_in

        # Apply specific sub-sector filtering
        if "All" not in selected_sub:
            if not any(opt in selected_sub for opt in special_options):
                summary_lf = summary_lf.filter(pl.col("category").is_in(selected_sub))

        summary_lf = (
            summary_lf.group_by(["category", "broad_sector"])
            .agg(
                [
                    pl.col("metadata_jobPostId").count().alias("Postings"),
                    pl.col("numberOfVacancies").sum().alias("Vacancies"),
                    pl.col("average_salary").median().alias("Median Salary"),
                    pl.col("minimumYearsExperience").mean().alias("Avg Exp"),
                    pl.col("metadata_totalNumberJobApplication")
                    .sum()
                    .alias("Applications"),
                    pl.col("metadata_totalNumberOfView").sum().alias("Views"),
                    (pl.col("Job Repost") == "Y").sum().alias("Job Reposts"),
                ]
            )
            .with_columns(
                [
                    # Calculate and explicitly round to 1 decimal place
                    ((pl.col("Vacancies") / total_mkt_vacancies) * 100)
                    .round(1)
                    .alias("% of all vacancies"),
                    ((pl.col("Applications") / total_mkt_apps) * 100)
                    .round(1)
                    .alias("% of all applications"),
                    (pl.col("Applications") / pl.col("Vacancies"))
                    .round(1)
                    .alias("Apps/Vac"),
                    (pl.col("Views") / pl.col("Postings")).round(1).alias("Views/Post"),
                    ((pl.col("Job Reposts") / pl.col("Postings")) * 100)
                    .round(1)
                    .alias("% Job Reposts"),
                ]
            )
            .join(sector_benchmarks, on="broad_sector")
            .join(top_apps_seniority, on="category")
        )

        # --- 4. APPLY TOP 10 LOGIC / SORTING ---
        if "Top 10 Most Competitive Sub Sectors" in selected_sub:
            summary_lf = summary_lf.sort("Apps/Vac", descending=True).limit(10)
        elif "Top 10 Sub Sectors with Highest Vacancies" in selected_sub:
            summary_lf = summary_lf.sort("Vacancies", descending=True).limit(10)
        elif "All" in selected_sub:
            summary_lf = summary_lf.sort("category")
        else:
            summary_lf = summary_lf.sort("broad_sector")

        # --- 5. TRANSFORM FOR DISPLAY ---
        display_df = summary_lf.collect().to_pandas()

        if not display_df.empty:
            display_df["Most Frequent Titles"] = display_df["category"].map(
                title_lookup_dict
            )

            def get_salary_indicator(row):
                diff = row["Median Salary"] - row["Parent Sector Median"]
                if diff > 0:
                    return "↑ Higher"
                elif diff < 0:
                    return "↓ Lower"
                else:
                    return "▬ Match"

            def get_exp_indicator(row):
                diff = row["Avg Exp"] - row["Parent Sector Avg Exp"]
                if diff > 0.2:
                    return "↑ More"
                elif diff < -0.2:
                    return "↓ Less"
                else:
                    return "▬ Similar"

            display_df["Salary vs Sector"] = display_df.apply(
                get_salary_indicator, axis=1
            )
            display_df["Exp vs Sector"] = display_df.apply(get_exp_indicator, axis=1)

        # --- 6. STYLING & DISPLAY ---
        def style_rows(row):
            bg_color = sector_colors.get(row["broad_sector"], "#1a1c24")
            hex_color = bg_color.lstrip("#")
            r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = "black" if brightness > 125 else "white"
            return [f"background-color: {bg_color}; color: {text_color}"] * len(row)

        # Format values strictly to 1 decimal place
        styled_df = display_df.style.apply(style_rows, axis=1).format(
            {
                "Median Salary": lambda x: f"S$ {x:,.0f}" if pd.notnull(x) else "-",
                "Parent Sector Median": lambda x: (
                    f"S$ {x:,.0f}" if pd.notnull(x) else "-"
                ),
                "Avg Exp": "{:.1f} yrs",
                "Parent Sector Avg Exp": "{:.1f} yrs",
                "Vacancies": "{:,.0f}",
                "% of all vacancies": "{:.1f}%",  # Strictly 1dp
                "Applications": "{:,.0f}",
                "% of all applications": "{:.1f}%",  # Strictly 1dp
                "Views": "{:,.0f}",
                "Job Reposts": "{:,.0f}",
                "Apps/Vac": "{:.1f}",
                "Views/Post": "{:.1f}",
                "% Job Reposts": "{:.1f}%",
            }
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_order=[
                "category",
                "broad_sector",
                "Vacancies",
                "% of all vacancies",
                "Applications",
                "% of all applications",
                "Apps/Vac",
                "Median Salary",
                "Salary vs Sector",
                "Parent Sector Median",
                "Avg Exp",
                "Exp vs Sector",
                "Parent Sector Avg Exp",
                "Top Seniority (Apps)",
                "Views",
                "Views/Post",
                "Job Reposts",
                "% Job Reposts",
                "Most Frequent Titles",
            ],
            column_config={
                "category": st.column_config.TextColumn("Sub-sector", width="medium"),
                "broad_sector": st.column_config.TextColumn(
                    "Parent Broad Sector", width=270
                ),
                "Vacancies": st.column_config.NumberColumn("Vacancies", width="small"),
                "% of all vacancies": st.column_config.NumberColumn(
                    "% Share Vacs", format="%.1f%%", width=115
                ),
                "Applications": st.column_config.NumberColumn(
                    "Total App", width="small"
                ),
                "% of all applications": st.column_config.NumberColumn(
                    "% Share Apps", format="%.1f%%", width=115
                ),
                "Apps/Vac": st.column_config.NumberColumn(
                    "Apps/Vac", format="%.1f", width="small"
                ),
                "Median Salary": st.column_config.TextColumn("Median $", width="small"),
                "Salary vs Sector": st.column_config.TextColumn(
                    "vs. Broad Sector", width=110
                ),
                "Parent Sector Median": st.column_config.TextColumn(
                    "Broad Sector Median", width=120
                ),
                "Avg Exp": st.column_config.TextColumn("Avg Exp", width="small"),
                "Exp vs Sector": st.column_config.TextColumn(
                    "vs. Sector Exp", width=110
                ),
                "Parent Sector Avg Exp": st.column_config.TextColumn(
                    "Broad Sector Avg Exp", width=120
                ),
                "Top Seniority (Apps)": st.column_config.TextColumn(
                    "Most Popular Seniority", width="medium"
                ),
                "Views": st.column_config.NumberColumn("Total Views", width="small"),
                "Views/Post": st.column_config.NumberColumn(
                    "Views per Post", width=100
                ),
                "Job Reposts": st.column_config.NumberColumn(
                    "Total Reposts", width=100
                ),
                "% Job Reposts": st.column_config.TextColumn(
                    "Job Repost Rate", width=100
                ),
                "Most Frequent Titles": st.column_config.TextColumn(
                    "Most Frequent Roles", width="large"
                ),
            },
        )

    # 4. CALL THE UPDATED SECTION
    render_summary_section(lf_filtered, dynamic_title_lookup, subsector_list)


# --- 5. RUN ---
render_main_dashboard(selected_range)

# Export
# csv = filtered_df.to_csv(index=False).encode('utf-8')
# st.download_button("📥 Export Filtered Database", data=csv, file_name='Job_Market_Data.csv', mime='text/csv')
