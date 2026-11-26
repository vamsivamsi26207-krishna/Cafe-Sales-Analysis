
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="CafeIQ | Smart Analytics",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CUSTOM CSS - DARK PURPLE THEME
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #0B0B12;
    color: #F5F3FF;
}

[data-testid="stSidebar"] {
    background-color: #171522;
    border-right: 1px solid #332448;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #F5F3FF;
}

.metric-card {
    background: linear-gradient(135deg, #211934, #171522);
    border: 1px solid #49306B;
    padding: 20px;
    border-radius: 14px;
    min-height: 115px;
}

.metric-label {
    color: #B9A8D5;
    font-size: 13px;
    font-weight: 600;
}

.metric-value {
    color: #C084FC;
    font-size: 27px;
    font-weight: bold;
    margin-top: 8px;
}

.section-card {
    background-color: #171522;
    border: 1px solid #332448;
    padding: 18px;
    border-radius: 12px;
}

.stButton button {
    background-color: #7C3AED;
    color: white;
    border-radius: 8px;
}

hr {
    border-color: #332448;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. DATA LOADING AND CLEANING
# ==========================================

@st.cache_data
def load_data(file):
    return pd.read_csv(file)


def clean_data(data):

    df = data.copy()

    # Remove duplicate records
    df = df.drop_duplicates()

    # Convert numerical columns
    numeric_columns = [
        "Quantity",
        "Price Per Unit",
        "Total Spent"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

    # Convert transaction date
    if "Transaction Date" in df.columns:
        df["Transaction Date"] = pd.to_datetime(
            df["Transaction Date"],
            errors="coerce"
        )

    # Remove negative business values
    if "Quantity" in df.columns:
        df.loc[df["Quantity"] < 0, "Quantity"] = np.nan

    if "Price Per Unit" in df.columns:
        df.loc[df["Price Per Unit"] < 0, "Price Per Unit"] = np.nan

    if "Total Spent" in df.columns:
        df.loc[df["Total Spent"] < 0, "Total Spent"] = np.nan

    return df


# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.markdown(
    """
    <h1 style='color:#C084FC;'>☕ CafeIQ</h1>
    <p style='color:#A1A1AA;'>
    SMART CAFE ANALYTICS PLATFORM
    </p>
    """,
    unsafe_allow_html=True
)

st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Overview",
        "Sales Analytics",
        "Product Insights",
        "Customer Insights",
        "Data Explorer",
        "Business Insights"
    ]
)

st.sidebar.divider()

st.sidebar.markdown("### DATA SOURCE")

uploaded_file = st.sidebar.file_uploader(
    "Upload Cafe Sales CSV (not only sales data, but also any cafe-related dataset)",
    type=["csv"]
)

# ==========================================
# 5. LOAD DATASET
# ==========================================

try:

    if uploaded_file is not None:
        raw_df = load_data(uploaded_file)

    else:
        file_path = Path(__file__).parent / "data" / "cafe_sales.csv"

        if file_path.exists():
            raw_df = load_data(str(file_path))
        else:
            st.title("☕ Welcome to CafeIQ")
            st.info(
                "Upload your cafe_sales.csv file "
                "using the sidebar to get started."
            )
            st.stop()

    df = clean_data(raw_df)

except Exception as e:
    st.error(f"Unable to load dataset: {e}")
    st.stop()


# ==========================================
# 6. VALIDATE DATASET
# ==========================================

required_columns = ["Item", "Total Spent"]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"Your dataset is missing required columns: "
        f"{missing_columns}"
    )
    st.stop()

if df.empty:
    st.warning("Your dataset contains no usable records.")
    st.stop()


# ==========================================
# 7. SIDEBAR FILTERS
# ==========================================

st.sidebar.markdown("### FILTER DATA")

filtered_df = df.copy()

if "Item" in df.columns:

    item_options = sorted(
        df["Item"].dropna().unique().tolist()
    )

    selected_items = st.sidebar.multiselect(
        "Products",
        item_options,
        default=item_options
    )

    filtered_df = filtered_df[
        filtered_df["Item"].isin(selected_items)
    ]

if "Payment Method" in df.columns:

    payment_options = sorted(
        df["Payment Method"].dropna().unique().tolist()
    )

    selected_payment = st.sidebar.multiselect(
        "Payment Methods",
        payment_options,
        default=payment_options
    )

    filtered_df = filtered_df[
        filtered_df["Payment Method"].isin(selected_payment)
    ]

if "Location" in df.columns:

    location_options = sorted(
        df["Location"].dropna().unique().tolist()
    )

    selected_locations = st.sidebar.multiselect(
        "Locations",
        location_options,
        default=location_options
    )

    filtered_df = filtered_df[
        filtered_df["Location"].isin(selected_locations)
    ]

if "Transaction Date" in df.columns:

    valid_dates = filtered_df["Transaction Date"].dropna()

    if not valid_dates.empty:

        date_range = st.sidebar.date_input(
            "Transaction Date Range",
            value=(
                valid_dates.min().date(),
                valid_dates.max().date()
            ),
            min_value=valid_dates.min().date(),
            max_value=valid_dates.max().date()
        )

        if isinstance(date_range, tuple) and len(date_range) == 2:

            start_date, end_date = date_range

            filtered_df = filtered_df[
                filtered_df["Transaction Date"].dt.date.between(
                    start_date, end_date
                )
            ]


if filtered_df.empty:
    st.warning("No records match your selected filters.")
    st.stop()


# ==========================================
# 8. COMMON METRICS
# ==========================================

revenue = filtered_df["Total Spent"].sum()

if "Transaction ID" in filtered_df.columns:
    transactions = filtered_df["Transaction ID"].nunique()
else:
    transactions = len(filtered_df)

if "Quantity" in filtered_df.columns:
    total_quantity = filtered_df["Quantity"].sum()
else:
    total_quantity = 0

average_order = (
    revenue / transactions if transactions > 0 else 0
)


# ==========================================
# 9. COMMON CHART CONFIGURATION
# ==========================================

def style_chart(fig):

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B0B12",
        plot_bgcolor="#171522",
        font=dict(color="#F5F3FF"),
        margin=dict(l=20, r=20, t=50, b=20),
        colorway=[
            "#A855F7",
            "#7C3AED",
            "#C084FC",
            "#9333EA",
            "#D8B4FE"
        ]
    )

    return fig


# ==========================================
# 10. KPI CARDS
# ==========================================

def show_metrics():

    c1, c2, c3, c4 = st.columns(4)

    metrics = [
        ("TOTAL REVENUE", f"₹{revenue:,.2f}"),
        ("TRANSACTIONS", f"{transactions:,}"),
        ("ITEMS SOLD", f"{total_quantity:,.0f}"),
        ("AVERAGE ORDER", f"₹{average_order:,.2f}")
    ]

    for col, (label, value) in zip(
        [c1, c2, c3, c4], metrics
    ):

        with col:

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ==========================================
# 11. OVERVIEW DASHBOARD
# ==========================================

if page == "Overview":

    st.title("☕ Cafe Performance Overview")

    st.caption(
        "Monitor your cafe's sales, revenue "
        "and product performance."
    )

    st.divider()

    show_metrics()

    st.write("")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Monthly Revenue")

        if "Transaction Date" in filtered_df.columns:

            monthly = (
                filtered_df.dropna(
                    subset=["Transaction Date"]
                )
                .assign(
                    Month=lambda x:
                    x["Transaction Date"].dt.to_period("M").astype(str)
                )
                .groupby("Month")["Total Spent"]
                .sum()
                .reset_index()
            )

            if not monthly.empty:

                fig = px.line(
                    monthly,
                    x="Month",
                    y="Total Spent",
                    markers=True,
                    title="Revenue Trend"
                )

                fig.update_traces(
                    line_color="#A855F7",
                    marker_color="#C084FC"
                )

                st.plotly_chart(
                    style_chart(fig),
                    use_container_width=True
                )

            else:
                st.info("No valid transaction dates available.")

        else:
            st.info("Transaction Date column not available.")

    with col2:

        st.subheader("Product Performance")

        product_sales = (
            filtered_df.groupby("Item")["Total Spent"]
            .sum()
            .reset_index()
            .sort_values("Total Spent", ascending=False)
        )

        fig = px.bar(
            product_sales,
            x="Item",
            y="Total Spent",
            color="Total Spent",
            color_continuous_scale="Purples",
            title="Revenue by Product"
        )

        st.plotly_chart(
            style_chart(fig),
            use_container_width=True
        )

    st.divider()

    st.subheader("Recent Transactions")

    st.dataframe(
        filtered_df.head(10),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 12. SALES ANALYTICS
# ==========================================

elif page == "Sales Analytics":

    st.title("📈 Sales Analytics")

    st.caption("Explore your cafe's sales performance.")

    show_metrics()

    st.write("")

    if "Transaction Date" in filtered_df.columns:

        monthly = (
            filtered_df.dropna(
                subset=["Transaction Date"]
            )
            .assign(
                Month=lambda x:
                x["Transaction Date"].dt.to_period("M").astype(str)
            )
            .groupby("Month")["Total Spent"]
            .sum()
            .reset_index()
        )

        if not monthly.empty:

            fig = px.area(
                monthly,
                x="Month",
                y="Total Spent",
                title="Monthly Sales Trend"
            )

            fig.update_traces(
                line_color="#A855F7",
                fillcolor="rgba(168,85,247,0.20)"
            )

            st.plotly_chart(
                style_chart(fig),
                use_container_width=True
            )

        daily = (
            filtered_df.dropna(
                subset=["Transaction Date"]
            )
            .groupby(
                filtered_df["Transaction Date"].dt.day_name()
            )["Total Spent"]
            .sum()
            .reset_index()
        )

        daily.columns = ["Day", "Revenue"]

        if not daily.empty:

            fig = px.bar(
                daily,
                x="Day",
                y="Revenue",
                title="Sales by Day of Week"
            )

            st.plotly_chart(
                style_chart(fig),
                use_container_width=True
            )

    else:

        st.info("Transaction Date column is unavailable.")


# ==========================================
# 13. PRODUCT INSIGHTS
# ==========================================

elif page == "Product Insights":

    st.title("🛍️ Product Insights")

    st.caption("Understand which products drive your revenue.")

    product_sales = (
        filtered_df.groupby("Item")
        .agg(
            Revenue=("Total Spent", "sum"),
            Transactions=("Total Spent", "count")
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )

    if "Quantity" in filtered_df.columns:

        quantity_data = (
            filtered_df.groupby("Item")["Quantity"]
            .sum()
            .reset_index()
        )

        product_sales = product_sales.merge(
            quantity_data,
            on="Item",
            how="left"
        )

    else:
        product_sales["Quantity"] = 0

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Top Selling Products")

        fig = px.bar(
            product_sales.head(5),
            x="Revenue",
            y="Item",
            orientation="h",
            color="Revenue",
            color_continuous_scale="Purples"
        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"})

        st.plotly_chart(
            style_chart(fig),
            use_container_width=True
        )

    with col2:

        st.subheader("Product Revenue Share")

        fig = px.pie(
            product_sales,
            names="Item",
            values="Revenue",
            hole=0.55,
            color_discrete_sequence=[
                "#A855F7",
                "#7C3AED",
                "#C084FC",
                "#9333EA",
                "#D8B4FE"
            ]
        )

        st.plotly_chart(
            style_chart(fig),
            use_container_width=True
        )

    st.subheader("Product Performance Table")

    st.dataframe(
        product_sales,
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# 14. CUSTOMER INSIGHTS
# ==========================================

elif page == "Customer Insights":

    st.title("👥 Customer Insights")

    st.caption(
        "Understand transaction patterns, "
        "payment preferences and location performance."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Payment Preferences")

        if "Payment Method" in filtered_df.columns:

            payment = (
                filtered_df["Payment Method"]
                .fillna("Unknown")
                .value_counts()
                .reset_index()
            )

            payment.columns = ["Payment Method", "Transactions"]

            fig = px.pie(
                payment,
                names="Payment Method",
                values="Transactions",
                hole=0.5
            )

            st.plotly_chart(
                style_chart(fig),
                use_container_width=True
            )

        else:
            st.info("Payment Method column unavailable.")

    with col2:

        st.subheader("Location Performance")

        if "Location" in filtered_df.columns:

            location = (
                filtered_df.groupby("Location")["Total Spent"]
                .sum()
                .reset_index()
                .sort_values("Total Spent", ascending=False)
            )

            fig = px.bar(
                location,
                x="Location",
                y="Total Spent",
                color="Total Spent",
                color_continuous_scale="Purples"
            )

            st.plotly_chart(
                style_chart(fig),
                use_container_width=True
            )

        else:
            st.info("Location column unavailable.")

    st.info(
        "Customer-level retention and repeat purchase "
        "analysis requires a customer identifier in the dataset."
    )


# ==========================================
# 15. DATA EXPLORER
# ==========================================

elif page == "Data Explorer":

    st.title("🗂️ Data Explorer")

    st.caption("Explore and inspect your cafe sales dataset.")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Rows", len(df))
    col2.metric("Total Columns", len(df.columns))
    col3.metric(
        "Duplicate Rows",
        int(raw_df.duplicated().sum())
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "Dataset Preview",
        "Data Quality",
        "Statistics"
    ])

    with tab1:

        st.subheader("Dataset Records")

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        st.subheader("Missing Values")

        missing = raw_df.isnull().sum().reset_index()

        missing.columns = ["Column", "Missing Values"]

        st.dataframe(
            missing,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Duplicate Records")

        st.write(
            f"Duplicate records detected: "
            f"{raw_df.duplicated().sum()}"
        )

        st.subheader("Data Types")

        st.write(raw_df.dtypes.astype(str))

    with tab3:

        st.subheader("Statistical Summary")

        st.dataframe(
            df.describe(include="all").T,
            use_container_width=True
        )

    csv_data = filtered_df.to_csv(index=False)

    st.download_button(
        "⬇ Download Filtered Dataset",
        data=csv_data,
        file_name="cafeiq_cleaned_data.csv",
        mime="text/csv"
    )


# ==========================================
# 16. BUSINESS INSIGHTS
# ==========================================

elif page == "Business Insights":

    st.title("💡 Business Insights")

    st.caption(
        "Turn sales data into useful business decisions."
    )

    product_sales = (
        filtered_df.groupby("Item")["Total Spent"]
        .sum()
        .sort_values(ascending=False)
    )

    if not product_sales.empty:

        best_product = product_sales.index[0]

        best_revenue = product_sales.iloc[0]

        st.markdown(
            f"""
            <div class="section-card">
                <h3 style="color:#C084FC;">
                🏆 Top Performing Product
                </h3>
                <h2>{best_product}</h2>
                <p>Revenue: ₹{best_revenue:,.2f}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        st.subheader("Business Recommendations")

        st.success(
            f"Focus on promoting {best_product}, "
            "which generates the highest revenue."
        )

        if len(product_sales) > 1:

            lowest_product = product_sales.index[-1]

            st.warning(
                f"Review the performance and pricing "
                f"of {lowest_product}."
            )

    if "Payment Method" in filtered_df.columns:

        most_used = (
            filtered_df["Payment Method"]
            .mode()
        )

        if not most_used.empty:

            st.info(
                f"Most frequently used payment method: "
                f"{most_used.iloc[0]}"
            )

    st.caption(
        "Recommendations are based on observed sales data, "
        "not guaranteed business outcomes."
    )


# ==========================================
# 17. FOOTER
# ==========================================

st.sidebar.divider()

st.sidebar.caption("CafeIQ v1.0")
st.sidebar.caption("Built with Python & Streamlit")

st.markdown("---")

st.caption(
    "CafeIQ | Smart Cafe Analytics Platform | "
    "Data-driven business intelligence"
)
