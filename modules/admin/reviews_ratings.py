import streamlit as st
import pandas as pd
import plotly.express as px
import os

def show_reviews_ratings(df_reviews, df_products, df_vendors=None, df_customers=None, df_orders=None):
    
    st.markdown(
        """
        <div style="background-color: #9370DB; padding: 20px 30px; border-radius: 0px; margin-left: -5rem; margin-right: -5rem; margin-top: -2rem; margin-bottom: 25px;">
            <h3 style="color: white; margin: 0; font-size: 32px;">⭐ Customer Reviews & Ratings Intelligence</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    
    # Defensive copies & empty dataframe initializations
    df_reviews = df_reviews.copy() if df_reviews is not None else pd.DataFrame()
    df_products = df_products.copy() if df_products is not None else pd.DataFrame()
    df_vendors = df_vendors.copy() if df_vendors is not None else pd.DataFrame()
    df_customers = df_customers.copy() if df_customers is not None else pd.DataFrame()

    # Fallback review dataset loading if missing
    if df_reviews.empty and os.path.exists("data/reviews.parquet"):
        try:
            df_reviews = pd.read_parquet("data/reviews.parquet")
        except Exception:
            df_reviews = pd.DataFrame()

    if "status" not in df_reviews.columns:
        df_reviews["status"] = "Published"

    if "rating" in df_reviews.columns:
        df_reviews["rating"] = pd.to_numeric(df_reviews["rating"], errors="coerce")

    if "created_at" in df_reviews.columns:
        df_reviews["created_at"] = pd.to_datetime(df_reviews["created_at"], errors="coerce")

    # Safe Merging across Products, Vendors, and Customers
    merged_reviews = df_reviews.copy()

    # STEP 1: Merge Product details (gives us 'product_name', 'category', AND 'vendor_id')
    if not merged_reviews.empty and not df_products.empty and "product_id" in merged_reviews.columns and "product_id" in df_products.columns:
        prod_cols = [c for c in ["product_id", "name", "category", "vendor_id"] if c in df_products.columns]
        merged_reviews = pd.merge(merged_reviews, df_products[prod_cols], on="product_id", how="left")
        if "name" in merged_reviews.columns:
            merged_reviews["product_name"] = merged_reviews["name"]

    # STEP 2: Merge Vendor details using vendor_id (obtained from df_products)
    if not merged_reviews.empty and not df_vendors.empty and "vendor_id" in merged_reviews.columns and "vendor_id" in df_vendors.columns:
        merged_reviews = pd.merge(merged_reviews, df_vendors[["vendor_id", "business_name"]], on="vendor_id", how="left")

    # STEP 3: Merge Customer details ("name" -> "full_name")
    if not merged_reviews.empty and not df_customers.empty and "customer_id" in merged_reviews.columns and "customer_id" in df_customers.columns:
        cust_cols = [c for c in ["customer_id", "name"] if c in df_customers.columns]
        merged_reviews = pd.merge(merged_reviews, df_customers[cust_cols], on="customer_id", how="left")
        if "name_y" in merged_reviews.columns:
            merged_reviews["full_name"] = merged_reviews["name_y"]
        elif "name" in merged_reviews.columns:
            merged_reviews["full_name"] = merged_reviews["name"]

    # STEP 4: Map Review Comments ("comment" -> "review_text")
    if "comment" in merged_reviews.columns:
        merged_reviews["review_text"] = merged_reviews["comment"]

    # Fill default display values for any unmapped or empty cells
    for col in ["product_name", "category", "business_name", "review_text", "full_name"]:
        if col not in merged_reviews.columns:
            merged_reviews[col] = "N/A"
        else:
            merged_reviews[col] = merged_reviews[col].fillna("N/A")

    # ==========================================
    # 🧮 PART 1: CORE REVIEWS & RATINGS KPIs
    # ==========================================
    total_reviews = len(merged_reviews)
    avg_rating = merged_reviews["rating"].mean() if total_reviews > 0 and "rating" in merged_reviews.columns else 0.0
    positive_reviews = (merged_reviews["rating"] >= 4).sum() if total_reviews > 0 and "rating" in merged_reviews.columns else 0
    satisfaction_rate = (positive_reviews / total_reviews * 100) if total_reviews > 0 else 0.0
    critical_reviews = (merged_reviews["rating"] <= 2).sum() if total_reviews > 0 and "rating" in merged_reviews.columns else 0

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
        <div style="background-color:#FEF9E7; padding:18px; border-radius:10px; border-left: 5px solid #F39C12;">
            <p style="margin:0; font-size:12px; color:#566573; font-weight:bold; text-transform:uppercase;">Overall Platform Rating</p>
            <h2 style="margin:5px 0 0 0; color:#D35400;">{avg_rating:.2f} / 5.0 ★</h2>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div style="background-color:#EBF5FB; padding:18px; border-radius:10px; border-left: 5px solid #2980B9;">
            <p style="margin:0; font-size:12px; color:#566573; font-weight:bold; text-transform:uppercase;">Total Customer Reviews</p>
            <h2 style="margin:5px 0 0 0; color:#1F618D;">{total_reviews:,}</h2>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
        <div style="background-color:#E8F8F5; padding:18px; border-radius:10px; border-left: 5px solid #2ECC71;">
            <p style="margin:0; font-size:12px; color:#566573; font-weight:bold; text-transform:uppercase;">Satisfaction Rate (4-5★)</p>
            <h2 style="margin:5px 0 0 0; color:#27AE60;">{satisfaction_rate:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
        <div style="background-color:#FDEDEC; padding:18px; border-radius:10px; border-left: 5px solid #E74C3C;">
            <p style="margin:0; font-size:12px; color:#566573; font-weight:bold; text-transform:uppercase;">Critical Feedback (1-2★)</p>
            <h2 style="margin:5px 0 0 0; color:#C0392B;">{critical_reviews:,}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================
    # 📊 PART 2: INTERACTIVE CHARTS
    # ==========================================
    
    st.markdown(
        """
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">📊 Platform Rating Analytics</h3>
        """,
        unsafe_allow_html=True,
    )


    if not merged_reviews.empty and "rating" in merged_reviews.columns and merged_reviews["rating"].notna().any():
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("#### 🌟 Star Rating Breakdown")
            rating_counts = merged_reviews["rating"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).reset_index()
            rating_counts.columns = ["Star Rating", "Count"]
            rating_counts["Star Rating"] = rating_counts["Star Rating"].astype(str) + " Star"

            fig_rating_bar = px.bar(
                rating_counts,
                x="Star Rating",
                y="Count",
                text="Count",
                labels={"Count": "Total Reviews", "Star Rating": "Rating Level"},
                color="Star Rating",
                color_discrete_sequence=["#E74C3C", "#E67E22", "#F1C40F", "#2ECC71", "#27AE60"]
            )
            fig_rating_bar.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320, showlegend=False)
            st.plotly_chart(fig_rating_bar, use_container_width=True)

        with chart_col2:
            st.markdown("#### 🏷️ Average Rating by Category")
            if "category" in merged_reviews.columns and merged_reviews["category"].notna().any():
                cat_ratings = merged_reviews.groupby("category")["rating"].mean().reset_index()
                cat_ratings = cat_ratings.sort_values(by="rating", ascending=True)

                fig_cat_bar = px.bar(
                    cat_ratings,
                    x="rating",
                    y="category",
                    orientation="h",
                    labels={"rating": "Average Rating (out of 5)", "category": "Category"},
                    color="rating",
                    color_continuous_scale="RdYlGn"
                )
                fig_cat_bar.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320, coloraxis_showscale=False)
                st.plotly_chart(fig_cat_bar, use_container_width=True)
            else:
                st.info("No category details available to render breakdown.")

        st.markdown("<br>", unsafe_allow_html=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            st.markdown("#### 📈 Average Satisfaction Trend Over Time")
            if "created_at" in merged_reviews.columns and merged_reviews["created_at"].notna().any():
                merged_reviews["date"] = merged_reviews["created_at"].dt.date
                trend_df = merged_reviews.dropna(subset=["date"]).groupby("date")["rating"].mean().reset_index()

                fig_trend = px.line(
                    trend_df,
                    x="date",
                    y="rating",
                    labels={"rating": "Avg Daily Rating", "date": "Date"},
                    markers=True,
                    color_discrete_sequence=["#2980B9"]
                )
                fig_trend.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320, yaxis_range=[1, 5])
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No timestamp data available for rating timeline.")

        with chart_col4:
            st.markdown("#### 🏬 Top Vendor Satisfaction Benchmark")
            valid_vendor_reviews = merged_reviews[merged_reviews["business_name"] != "N/A"]
            if "business_name" in merged_reviews.columns and not valid_vendor_reviews.empty:
                vendor_ratings = valid_vendor_reviews.groupby("business_name")["rating"].mean().reset_index()
                vendor_ratings = vendor_ratings.sort_values(by="rating", ascending=False).head(8)

                fig_vendor = px.bar(
                    vendor_ratings,
                    x="rating",
                    y="business_name",
                    orientation="h",
                    labels={"rating": "Avg Rating (★)", "business_name": "Vendor Store"},
                    color="rating",
                    color_continuous_scale="Viridis"
                )
                fig_vendor.update_layout(
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=320,
                    coloraxis_showscale=False,
                    xaxis_range=[1, 5],
                    yaxis={'categoryorder': 'total ascending'}
                )
                st.plotly_chart(fig_vendor, use_container_width=True)
            else:
                st.info("No vendor metadata linked with customer feedback.")
    else:
        st.info("No customer ratings or review metrics available for chart generation.")

    st.markdown("---")

    # ==========================================
    # 🛡️ PART 3: ADMIN MODERATION QUEUE
    # ==========================================
    
    st.markdown(
        """
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">🛡️ Customer Review Moderation & Feedback Inspection</h3>
        """,
        unsafe_allow_html=True,
    )


    if not merged_reviews.empty:
        filter_col1, filter_col2 = st.columns([2, 2])
        with filter_col1:
            rating_filter = st.multiselect(
                "Filter Ratings",
                options=[1, 2, 3, 4, 5],
                default=[1, 2, 3, 4, 5],
                key="rating_filter_select"
            )
        with filter_col2:
            status_filter = st.selectbox(
                "Filter Status",
                options=["All", "Published", "Flagged", "Critical Only (1-2 Stars)"],
                index=0,
                key="status_filter_select"
            )

        # Apply filters
        display_reviews = merged_reviews.copy()
        if rating_filter:
            display_reviews = display_reviews[display_reviews["rating"].isin(rating_filter)]

        if status_filter == "Published":
            display_reviews = display_reviews[display_reviews["status"] == "Published"]
        elif status_filter == "Flagged":
            display_reviews = display_reviews[display_reviews["status"] == "Flagged"]
        elif status_filter == "Critical Only (1-2 Stars)":
            display_reviews = display_reviews[display_reviews["rating"] <= 2]

        cols_to_show = ["review_id", "product_name", "business_name", "full_name", "rating", "review_text", "status"]
        existing_cols = [c for c in cols_to_show if c in display_reviews.columns]

        st.dataframe(
            display_reviews[existing_cols].rename(
                columns={
                    "review_id": "ID",
                    "product_name": "Product",
                    "business_name": "Vendor",
                    "full_name": "Customer",
                    "rating": "Rating (★)",
                    "review_text": "Customer Comment",
                    "status": "Status"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("##### ⚡ Moderation Controls")
        mod_col1, mod_col2, mod_col3 = st.columns([2, 1, 1])

        if "review_id" in display_reviews.columns and not display_reviews.empty:
            review_ids = display_reviews["review_id"].tolist()
            with mod_col1:
                selected_review_id = st.selectbox(
                    "Select Review ID to Action",
                    options=review_ids,
                    key="review_action_select"
                )

            with mod_col2:
                if st.button("🚩 Flag Review", use_container_width=True, key=f"flag_{selected_review_id}"):
                    df_reviews.loc[df_reviews["review_id"] == selected_review_id, "status"] = "Flagged"
                    os.makedirs("data", exist_ok=True)
                    try:
                        df_reviews.to_parquet("data/reviews.parquet", index=False)
                        st.warning(f"Flagged Review #{selected_review_id} for vendor compliance audit.")
                    except Exception as e:
                        st.error(f"Failed to update status: {e}")
                    st.rerun()

            with mod_col3:
                if st.button("🟢 Approve / Publish", use_container_width=True, key=f"pub_{selected_review_id}"):
                    df_reviews.loc[df_reviews["review_id"] == selected_review_id, "status"] = "Published"
                    os.makedirs("data", exist_ok=True)
                    try:
                        df_reviews.to_parquet("data/reviews.parquet", index=False)
                        st.success(f"Approved and published Review #{selected_review_id}.")
                    except Exception as e:
                        st.error(f"Failed to update status: {e}")
                    st.rerun()
    else:
        st.info("No reviews available for moderation.")

    st.markdown("---")

    # ==========================================
    # 🏆 PART 4: PRODUCT & VENDOR QUALITY LEADERBOARD
    # ==========================================
    
    st.markdown(
        """
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">🏆 Product Quality Leaderboard</h3>
        """,
        unsafe_allow_html=True,
    )

    if not merged_reviews.empty and "product_name" in merged_reviews.columns and "rating" in merged_reviews.columns:
        product_summary = merged_reviews.groupby(["product_name", "business_name"]).agg(
            total_reviews=("rating", "count"),
            avg_rating=("rating", "mean"),
            critical_count=("rating", lambda x: (x <= 2).sum())
        ).reset_index()

        product_summary = product_summary.sort_values(by="avg_rating", ascending=False).reset_index(drop=True)
        product_summary.index += 1

        st.dataframe(
            product_summary.rename(
                columns={
                    "product_name": "Product Name",
                    "business_name": "Vendor Store",
                    "total_reviews": "Total Reviews",
                    "avg_rating": "Average Score (★)",
                    "critical_count": "Critical Reviews (1-2★)"
                }
            ),
            use_container_width=True
        )
    else:
        st.info("No aggregated review metrics available.")