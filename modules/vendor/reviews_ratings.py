import streamlit as st
import pandas as pd
import os

def render_kpi_card(category_title: str, main_value: str, sub_label: str):
    """
    Renders custom HTML/CSS KPI cards matching the boxed, blue-accent card UI design.
    """
    card_html = f"""
    <div style="
        border: 1.5px solid #E2E8F0;
        border-top: 4px solid #4F46E5;
        border-radius: 8px;
        padding: 16px 12px;
        background-color: #FFFFFF;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    ">
        <div style="
            font-size: 11px;
            font-weight: 700;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 8px;
        ">{category_title}</div>
        <div style="
            font-size: 20px;
            font-weight: 800;
            color: #1E293B;
            margin-bottom: 6px;
            line-height: 1.2;
        ">{main_value}</div>
        <div style="
            font-size: 13px;
            font-weight: 600;
            color: #4F46E5;
        ">{sub_label}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def show_reviews_ratings(vendor_id: int, df_products: pd.DataFrame, df_reviews: pd.DataFrame = None, df_items: pd.DataFrame = None):
    """
    Vendor Reviews & Ratings Workspace Module.
    Guarantees strict data isolation: Vendors can ONLY view reviews and metrics
    associated with products assigned to their vendor_id.
    """
    st.title("⭐ Reviews & Ratings Workspace")
    st.caption("Monitor customer feedback, catalog sentiment, and product rating analytics.")

    # -------------------------------------------------------------------------
    # 1. Fallback & Data Safety Verification
    # -------------------------------------------------------------------------
    if df_reviews is None or df_reviews.empty:
        reviews_path = "data/reviews.parquet"
        if os.path.exists(reviews_path):
            df_reviews = pd.read_parquet(reviews_path)
        else:
            st.warning("⚠️ No reviews data source found (`data/reviews.parquet`).")
            return

    if df_products is None or df_products.empty:
        st.warning("⚠️ Products dataset is missing or empty.")
        return

    # Normalize data types
    vendor_id = int(vendor_id)
    df_products = df_products.copy()
    df_products["vendor_id"] = df_products["vendor_id"].astype(int)
    df_products["product_id"] = df_products["product_id"].astype(int)

    df_reviews = df_reviews.copy()
    if "product_id" in df_reviews.columns:
        df_reviews["product_id"] = df_reviews["product_id"].astype(int)

    # -------------------------------------------------------------------------
    # 2. Whitelist Data Isolation (Logged-In Vendor Products Only)
    # -------------------------------------------------------------------------
    vendor_products = df_products[df_products["vendor_id"] == vendor_id]

    if vendor_products.empty:
        st.info("ℹ️ You do not have any products registered in the catalog.")
        return

    # INNER JOIN guarantees reviews belonging to other vendors are strictly purged
    merged_reviews = pd.merge(
        df_reviews,
        vendor_products[["product_id", "name", "category", "price"]],
        on="product_id",
        how="inner"
    )

    if merged_reviews.empty:
        st.info("ℹ️ No customer reviews have been submitted for your products yet.")
        return

    # Convert Unix timestamps (ms) to Datetime
    if "created_at" in merged_reviews.columns:
        merged_reviews["review_date"] = pd.to_datetime(merged_reviews["created_at"], unit="ms", errors="coerce")
        merged_reviews["month_year"] = merged_reviews["review_date"].dt.to_period("M").astype(str)

    # -------------------------------------------------------------------------
    # 3. TOP BAR: Global Interactive Filters
    # -------------------------------------------------------------------------
    st.subheader("🔍 Search & Filter")
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 1])

    with f_col1:
        categories = ["All Categories"] + sorted(list(vendor_products["category"].dropna().unique()))
        selected_cat = st.selectbox("Category Filter", options=categories)

    with f_col2:
        prod_list = ["All Products"] + sorted(list(vendor_products["name"].unique()))
        selected_prod = st.selectbox("Product Search", options=prod_list)

    with f_col3:
        rating_list = ["All Ratings", "5 Stars", "4 Stars", "3 Stars", "2 Stars", "1 Star"]
        selected_rating_str = st.selectbox("Star Rating", options=rating_list)

    with f_col4:
        sort_order = st.selectbox("Sort Date", options=["Newest First", "Oldest First"])

    # Apply Filters
    filtered_df = merged_reviews.copy()

    if selected_cat != "All Categories":
        filtered_df = filtered_df[filtered_df["category"] == selected_cat]

    if selected_prod != "All Products":
        filtered_df = filtered_df[filtered_df["name"] == selected_prod]

    if selected_rating_str != "All Ratings":
        target_star = int(selected_rating_str.split()[0])
        filtered_df = filtered_df[filtered_df["rating"] == target_star]

    if "review_date" in filtered_df.columns:
        ascending = True if sort_order == "Oldest First" else False
        filtered_df = filtered_df.sort_values(by="review_date", ascending=ascending)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # ROW 1 — Custom Styled Box KPI Cards
    # -------------------------------------------------------------------------
    avg_rating = merged_reviews["rating"].mean()
    total_reviews_count = len(merged_reviews)
    positive_reviews = len(merged_reviews[merged_reviews["rating"] >= 4])
    critical_1star = len(merged_reviews[merged_reviews["rating"] == 1])
    positive_pct = (positive_reviews / total_reviews_count * 100) if total_reviews_count > 0 else 0
    rated_products_count = merged_reviews["product_id"].nunique()

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        render_kpi_card("RATING OVERALL", f"{avg_rating:.2f} / 5.0 ⭐", "Average Score")

    with kpi2:
        render_kpi_card("FEEDBACK VOLUME", f"{total_reviews_count:,}", "Total Reviews")

    with kpi3:
        render_kpi_card("CUSTOMER SENTIMENT", f"{positive_pct:.1f}%", "Positive Feedback")

    with kpi4:
        render_kpi_card("CRITICAL ALERTS", f"{critical_1star}", "1-Star Ratings")

    with kpi5:
        render_kpi_card("CATALOG COVERAGE", f"{rated_products_count} Items", "Active Products")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # ROW 2 — Analytics & Visual Charts
    # -------------------------------------------------------------------------
    st.subheader("📈 Ratings & Sentiment Analytics")
    c_col1, c_col2 = st.columns(2)

    with c_col1:
        st.markdown("**Star Rating Distribution**")
        rating_counts = merged_reviews["rating"].value_counts().reindex([5, 4, 3, 2, 1], fill_value=0)
        chart_data_dist = pd.DataFrame({"Star Rating": [f"{i} Stars" for i in rating_counts.index], "Count": rating_counts.values})
        st.bar_chart(chart_data_dist.set_index("Star Rating"))

    with c_col2:
        st.markdown("**Rating Trend Over Time**")
        if "month_year" in merged_reviews.columns and not merged_reviews["month_year"].empty:
            trend_df = merged_reviews.groupby("month_year")["rating"].mean().reset_index()
            trend_df = trend_df.sort_values("month_year").set_index("month_year")
            st.line_chart(trend_df)
        else:
            st.info("Insufficient timestamp data for historical trend chart.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # ROW 3 — Priority Action Items
    # -------------------------------------------------------------------------
    st.subheader("🚨 Priority Action Items")
    alert_col1, alert_col2 = st.columns(2)

    with alert_col1:
        critical_df = merged_reviews[merged_reviews["rating"] == 1]
        st.markdown(f"**Critical Customer Feedback ({len(critical_df)})**")
        if not critical_df.empty:
            for _, c_row in critical_df.head(3).iterrows():
                st.error(f"🔴 **{c_row['name']}** (Cust #{c_row['customer_id']}): \"{c_row['comment']}\"")
        else:
            st.success("✅ No 1-star critical reviews flagged.")

    with alert_col2:
        low_rated_prods = (
            merged_reviews.groupby(["product_id", "name"])["rating"]
            .mean()
            .reset_index()
        )
        underperforming = low_rated_prods[low_rated_prods["rating"] < 3.0]
        st.markdown(f"**Products Needing Attention ({len(underperforming)})**")
        if not underperforming.empty:
            for _, u_row in underperforming.iterrows():
                st.warning(f"⚠️ **{u_row['name']}** — Avg Rating: {u_row['rating']:.2f}/5.0")
        else:
            st.success("✅ All catalog products maintain a rating ≥ 3.0.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # ROW 4 — Customer Reviews Feed
    # -------------------------------------------------------------------------
    st.subheader(f"💬 Customer Reviews Feed ({len(filtered_df)})")

    if filtered_df.empty:
        st.info("No customer reviews match your active filter criteria.")
        return

    for _, row in filtered_df.iterrows():
        stars = "⭐" * int(row["rating"])
        date_str = row["review_date"].strftime("%b %d, %Y") if pd.notnull(row.get("review_date")) else "N/A"

        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{row['name']}** — {stars} (`{row['rating']}/5.0`)")
            with col_b:
                st.caption(f"🗓️ {date_str} | Customer #{row['customer_id']}")

            st.write(f"\"{row['comment']}\"")
            st.divider()