import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def show_customer_analytics(df_customers, df_orders):
    st.subheader("👤 Customer Performance & ML Segmentation Portal")
    
    # Ensure timestamps are parsed properly
    df_orders = df_orders.copy()
    df_orders["created_at"] = pd.to_datetime(df_orders["created_at"])
    
    # Filter for active, successful orders (exclude cancelled)
    valid_orders = df_orders[df_orders["status"] != "Cancelled"]

    # ==========================================
    # 🧮 PART 1: CORE CUSTOMER LIFECYCLE KPIs (All 5 Required)
    # ==========================================
    st.markdown("### 📈 Core Customer Metrics")
    
    # 1. Total Customers in system
    total_cust = df_customers["customer_id"].nunique()
    
    # Calculate order counts per customer
    orders_per_cust = valid_orders.groupby("customer_id")["order_id"].count()
    
    # 2. Returning Customers (Customers with more than 1 purchase)
    returning_cust_count = int((orders_per_cust > 1).sum())
    
    # 3. New Customers (Customers with exactly 1 purchase or registered without orders yet)
    new_cust_count = total_cust - returning_cust_count
    
    # 4. Retention Rate (%)
    retention_rate = (returning_cust_count / total_cust * 100) if total_cust > 0 else 0.0
    
    # 5. Churn Rate (%) (Define churn as customers inactive for more than 60 days)
    max_date = valid_orders["created_at"].max()
    last_purchase = valid_orders.groupby("customer_id")["created_at"].max()
    days_since_last_purchase = (max_date - last_purchase).dt.days
    churned_cust_count = int((days_since_last_purchase > 60).sum())
    churn_rate = (churned_cust_count / total_cust * 100) if total_cust > 0 else 0.0

    # 6. Average Customer Lifetime Value (CLV)
    clv_per_cust = valid_orders.groupby("customer_id")["total_amount"].sum()
    avg_clv = clv_per_cust.mean() if not clv_per_cust.empty else 0.0

    # Layout all 5 KPI Cards cleanly
    kpi_cols = st.columns(5)
    
    with kpi_cols[0]:
        st.markdown(f"""
        <div style="background-color:#EBF5FB; padding:15px; border-radius:8px; border-bottom: 4px solid #2980B9; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">🆕 NEW CUSTOMERS</p>
            <h3 style="margin:5px 0 0 0; color:#2C3E50;">{new_cust_count:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[1]:
        st.markdown(f"""
        <div style="background-color:#EAF2F8; padding:15px; border-radius:8px; border-bottom: 4px solid #1F618D; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">🔄 RETURNING</p>
            <h3 style="margin:5px 0 0 0; color:#1B4F72;">{returning_cust_count:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[2]:
        st.markdown(f"""
        <div style="background-color:#E8F8F5; padding:15px; border-radius:8px; border-bottom: 4px solid #16A085; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">📈 RETENTION RATE</p>
            <h3 style="margin:5px 0 0 0; color:#0E6251;">{retention_rate:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[3]:
        st.markdown(f"""
        <div style="background-color:#FDEDEC; padding:15px; border-radius:8px; border-bottom: 4px solid #E74C3C; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">🥀 CHURN RATE</p>
            <h3 style="margin:5px 0 0 0; color:#78281F;">{churn_rate:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[4]:
        st.markdown(f"""
        <div style="background-color:#FCF3CF; padding:15px; border-radius:8px; border-bottom: 4px solid #F1C40F; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">💎 AVERAGE CLV</p>
            <h3 style="margin:5px 0 0 0; color:#7D6608;">${avg_clv:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📊 PART 2: CORE LIFECYCLE CHARTS (Exactly Two)
    # ==========================================
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### 🍕 Customer Base Composition")
        # Chart 1: Donut showing breakdown of New vs. Returning customers
        composition_df = pd.DataFrame({
            "Customer Status": ["New Customers", "Returning Customers"],
            "Headcount": [new_cust_count, returning_cust_count]
        })
        fig_composition = px.pie(
            composition_df,
            names="Customer Status",
            values="Headcount",
            hole=0.5,
            color="Customer Status",
            color_discrete_map={"New Customers": "#3498DB", "Returning Customers": "#16A085"}
        )
        fig_composition.update_layout(margin=dict(l=15, r=15, t=10, b=10), height=300, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_composition, use_container_width=True)
        
    with chart_col2:
        st.markdown("#### ⚖️ Retention vs. Churn Rates")
        # Chart 2: Bar chart contrasting Retention Rate vs Churn Rate directly
        rate_df = pd.DataFrame({
            "Metric Category": ["Retention Rate", "Churn Rate"],
            "Percentage (%)": [retention_rate, churn_rate]
        })
        fig_rates = px.bar(
            rate_df,
            x="Metric Category",
            y="Percentage (%)",
            color="Metric Category",
            color_discrete_map={"Retention Rate": "#2ECC71", "Churn Rate": "#E74C3C"},
            text_auto=".1f"
        )
        fig_rates.update_layout(margin=dict(l=15, r=15, t=10, b=10), height=300, showlegend=False)
        st.plotly_chart(fig_rates, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # 🧬 PART 3: K-MEANS CUSTOMER SEGMENTATION
    # ==========================================
    st.markdown("### 🧬 Machine Learning: Customer Segmentation")
    st.caption("Using K-Means Clustering to automatically sort customers into 4 strategic value tiers based on purchase dynamics.")

    # Calculate Recency, Frequency, and Monetary (RFM) per customer
    rfm = valid_orders.groupby("customer_id").agg({
        "created_at": lambda x: (max_date - x.max()).days,  # Recency
        "order_id": "count",                              # Frequency
        "total_amount": "sum"                              # Monetary
    }).reset_index()
    
    rfm.columns = ["customer_id", "recency", "frequency", "monetary"]
    rfm = rfm.fillna(0)

    # ML Algorithm logic block
    if len(rfm) >= 4:
        # Standardize features for structural distance clustering
        scaler = StandardScaler()
        rfm_scaled = scaler.fit_transform(rfm[["recency", "frequency", "monetary"]])

        # Model instantiation for exactly 4 target groups
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        rfm["cluster"] = kmeans.fit_predict(rfm_scaled)

        # Calculate cluster centroids to map labels dynamically to high/low parameters
        centroids = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean()
        
        # Determine labels: Low recency, high frequency, high spend = Premium
        # High recency, low frequency, low spend = Inactive
        sorted_by_monetary = centroids.sort_values(by="monetary", ascending=False).index.tolist()
        
        tier_mapping = {
            sorted_by_monetary[0]: "Premium",
            sorted_by_monetary[1]: "Regular",
            sorted_by_monetary[2]: "Occasional",
            sorted_by_monetary[3]: "Inactive"
        }
        rfm["segment"] = rfm["cluster"].map(tier_mapping)
    else:
        # Fallback allocation if data profile is too sparse for ML pipeline
        rfm["segment"] = "Regular"
        if len(rfm) > 0: rfm.loc[0, "segment"] = "Premium"

    # Merge labels back into directory catalog
    customer_directory = pd.merge(df_customers, rfm[["customer_id", "recency", "frequency", "monetary", "segment"]], on="customer_id", how="left")
    customer_directory["segment"] = customer_directory["segment"].fillna("Inactive")
    customer_directory["monetary"] = customer_directory["monetary"].fillna(0.0)

    # Render Segmentation visual comparisons
    seg_col1, seg_col2 = st.columns(2)
    
    with seg_col1:
        st.markdown("#### 🍕 Cluster Representation Share")
        seg_counts = customer_directory["segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Total Count"]
        
        fig_seg_pie = px.pie(
            seg_counts,
            names="Segment",
            values="Total Count",
            color="Segment",
            color_discrete_map={
                "Premium": "#2ECC71",    # Green
                "Regular": "#3498DB",    # Blue
                "Occasional": "#F1C40F", # Yellow
                "Inactive": "#E74C3C"    # Red
            }
        )
        fig_seg_pie.update_layout(margin=dict(l=15, r=15, t=10, b=10), height=300, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig_seg_pie, use_container_width=True)
        
    with seg_col2:
        st.markdown("#### 🎯 Segment Profile Spending Limits")
        seg_spend = customer_directory.groupby("segment")["monetary"].mean().reset_index()
        
        fig_seg_bar = px.bar(
            seg_spend,
            x="segment",
            y="monetary",
            color="segment",
            labels={"segment": "Assigned Segment", "monetary": "Avg Lifetime Spend ($)"},
            color_discrete_map={
                "Premium": "#2ECC71",
                "Regular": "#3498DB",
                "Occasional": "#F1C40F",
                "Inactive": "#E74C3C"
            }
        )
        fig_seg_bar.update_layout(margin=dict(l=15, r=15, t=10, b=10), height=300, showlegend=False)
        st.plotly_chart(fig_seg_bar, use_container_width=True)

    # ==========================================
    # 🗂️ PART 4: DIRECTORY VIEW (Robust Column Mapping)
    # ==========================================
    st.markdown("### 🔍 Segment Explorer Directory")
    
    selected_tier = st.selectbox("Search Customer Profiles by ML Segment Group", ["All Segments", "Premium", "Regular", "Occasional", "Inactive"])
    
    directory_display = customer_directory.copy()
    if selected_tier != "All Segments":
        directory_display = directory_display[directory_display["segment"] == selected_tier]
        
    # Dynamically match and resolve names/emails based on whatever columns actually exist in the parquet file
    all_cols = directory_display.columns.tolist()
    
    # 1. Resolve Name
    if "first_name" in all_cols and "last_name" in all_cols:
        directory_display["Customer Name"] = directory_display["first_name"] + " " + directory_display["last_name"]
    elif "name" in all_cols:
        directory_display["Customer Name"] = directory_display["name"]
    elif "username" in all_cols:
        directory_display["Customer Name"] = directory_display["username"]
    else:
        directory_display["Customer Name"] = "Customer #" + directory_display["customer_id"].astype(str)

    # 2. Resolve Contact/Email
    email_col = next((c for c in ["email", "email_address", "contact"] if c in all_cols), None)
    if email_col:
        directory_display["Contact Email"] = directory_display[email_col]
    else:
        directory_display["Contact Email"] = "N/A"

    # Select only our safely resolved columns to display
    display_subset = directory_display[["customer_id", "Customer Name", "Contact Email", "segment", "monetary"]].rename(
        columns={
            "customer_id": "ID",
            "segment": "ML Segment Group",
            "monetary": "Total Spend ($)"
        }
    )
        
    st.dataframe(
        display_subset,
        use_container_width=True,
        hide_index=True
    )