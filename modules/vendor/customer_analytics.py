import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import plotly.express as px

def show_customer_analytics(vendor_id, df_items, df_orders, df_customers):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .customer-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #3182ce;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            text-align: center;
        }
        .customer-label {
            font-size: 0.8rem;
            color: #4a5568;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .customer-value {
            font-size: 1.6rem;
            color: #1a202c;
            font-weight: 700;
            margin: 4px 0;
        }
        .customer-footer {
            font-size: 0.75rem;
            color: #718096;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("👥 Advanced Customer Insights & ML Behavior Segmentation")
    st.caption("Track consumer retention health, calculate cohort lifecycles, and discover behavioral clusters with K-Means.")

    # =========================================================================
    # 🧮 STEP 1: CUSTOMER ANALYTICS COHORT ENGINE
    # =========================================================================
    # Filter transaction lines belonging to this vendor
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy()
    
    if my_items.empty or df_orders.empty:
        st.info("👥 No client transaction histories are logged for your store products yet.")
        return

    my_items["gross_line"] = my_items["quantity"] * my_items["price_per_unit"]
    
    # Merge to tie items back to their parent orders and buyer credentials
    customer_master = pd.merge(my_items, df_orders[["order_id", "customer_id", "status"]], on="order_id", how="inner")
    
    # Exclude failed checkouts for high data fidelity
    customer_master = customer_master[~customer_master["status"].isin(["Cancelled", "Failed"])]
    
    if customer_master.empty:
        st.info("⏳ Processing metrics. Valid consumer order receipts not finalized yet.")
        return

    # Calculate shopper order frequencies to identify retention rates
    shopper_frequency = customer_master.groupby("customer_id").agg(
        total_spent=("gross_line", "sum"),
        order_count=("order_id", "nunique")
    ).reset_index()

    # Define Core Cohort Metrics
    total_unique_shoppers = len(shopper_frequency)
    returning_shoppers_df = shopper_frequency[shopper_frequency["order_count"] > 1]
    returning_shoppers_count = len(returning_shoppers_df)
    new_shoppers_count = total_unique_shoppers - returning_shoppers_count

    # ● Retention & Churn Rates
    retention_rate = (returning_shoppers_count / total_unique_shoppers * 100) if total_unique_shoppers > 0 else 0.0
    churn_rate = 100.0 - retention_rate

    # ● Customer Lifetime Value (CLV)
    clv_mean = shopper_frequency["total_spent"].mean() if total_unique_shoppers > 0 else 0.0

    # =========================================================================
    # 🎛️ STEP 2: HIGH-FIDELITY UX COHORT KPI CARDS
    # =========================================================================
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    
    with kpi_col1:
        st.markdown(f"""
            <div class="customer-card" style="border-top-color: #4299e1;">
                <div class="customer-label">New</div>
                <div class="customer-value">{new_shoppers_count:,}</div>
                <div class="customer-footer">Single-purchase profiles</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
            <div class="customer-card" style="border-top-color: #319795;">
                <div class="customer-label">Returning</div>
                <div class="customer-value">{returning_shoppers_count:,}</div>
                <div class="customer-footer">Repeat brand interaction</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
            <div class="customer-card" style="border-top-color: #48bb78;">
                <div class="customer-label">Retention</div>
                <div class="customer-value">{retention_rate:.1f}%</div>
                <div class="customer-footer">Loyalty return rate velocity</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
            <div class="customer-card" style="border-top-color: #f56565;">
                <div class="customer-label">Churn</div>
                <div class="customer-value">{churn_rate:.1f}%</div>
                <div class="customer-footer">Single-visit bounce probabilities</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col5:
        st.markdown(f"""
            <div class="customer-card" style="border-top-color: #9b59b6;">
                <div class="customer-label">Mean CLV</div>
                <div class="customer-value">${clv_mean:,.2f}</div>
                <div class="customer-footer">Average lifetime revenue share</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 🤖 STEP 3: ML CUSTOMER SEGMENTATION ENGINE (K-MEANS CLUSTERING)
    # =========================================================================
    st.subheader("🤖 Machine Learning Segmentations (K-Means Clustering)")
    
    # Prepare clustering features matrix (Spent vs Volume Count)
    X = shopper_frequency[["total_spent", "order_count"]].copy()
    
    # We enforce exactly 4 groups to explicitly isolate: Premium, Regular, Occasional, Inactive
    n_clusters = 4
    
    if len(X) >= n_clusters:
        # Fit K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        shopper_frequency["cluster_id"] = kmeans.fit_predict(X)
        
        # Intelligently map generated cluster labels to requested target marketing groups 
        # based on overall purchasing power (total_spent)
        cluster_means = shopper_frequency.groupby("cluster_id")["total_spent"].mean().sort_values(ascending=False).index
        
        group_mapping = {
            cluster_means[0]: "👑 Premium Shoppers",
            cluster_means[1]: "🛍️ Regular Patrons",
            cluster_means[2]: "🕒 Occasional Visitors",
            cluster_means[3]: "💤 Inactive Profiles"
        }
        shopper_frequency["Segment Group"] = shopper_frequency["cluster_id"].map(group_mapping)
        
        # Display breakdown chart
        chart_col1, chart_col2 = st.columns([3, 2])
        
        with chart_col1:
            st.markdown("##### 📍 K-Means Multi-Dimensional Scatter Grouping")
            fig_scatter = px.scatter(
                shopper_frequency, x="order_count", y="total_spent",
                color="Segment Group",
                labels={"order_count": "Total Orders Placed Count", "total_spent": "Cumulative Gross Spending ($)"},
                color_discrete_map={
                    "👑 Premium Shoppers": "#9b59b6",
                    "🛍️ Regular Patrons": "#3498db",
                    "🕒 Occasional Visitors": "#e67e22",
                    "💤 Inactive Profiles": "#95a5a6"
                },
                hover_data=["customer_id"]
            )
            fig_scatter.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with chart_col2:
            st.markdown("##### 📊 Share of Consumer Segments")
            segment_counts = shopper_frequency["Segment Group"].value_counts().reset_index()
            
            fig_pie = px.pie(
                segment_counts, values="count", names="Segment Group",
                hole=0.4,
                color="Segment Group",
                color_discrete_map={
                    "👑 Premium Shoppers": "#9b59b6",
                    "🛍️ Regular Patrons": "#3498db",
                    "🕒 Occasional Visitors": "#e67e22",
                    "💤 Inactive Profiles": "#95a5a6"
                }
            )
            fig_pie.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig_pie, use_container_width=True)
            
        # Optional detail expander table
        with st.expander("🔍 Inspect Full Segment Allocation Directory"):
            # =========================================================================
            # 👥 SAFE CUSTOMER DIRECTORY MERGE
            # =========================================================================
            if not df_customers.empty and "customer_id" in df_customers.columns:
                # Dynamically determine which columns exist in the dataset to prevent KeyErrors
                available_cols = ["customer_id"]
                if "name" in df_customers.columns:
                    available_cols.append("name")
                if "email" in df_customers.columns:
                    available_cols.append("email")
                    
                # Merge using only the columns that actually exist
                detailed_report = pd.merge(
                    shopper_frequency, 
                    df_customers[available_cols], 
                    on="customer_id", 
                    how="left"
                )
                
                # Dynamically create fallback labels if some metadata columns are missing
                if "name" not in detailed_report.columns:
                    detailed_report["name"] = detailed_report["customer_id"].apply(lambda idx: f"Customer #{idx}")
                if "email" not in detailed_report.columns:
                    detailed_report["email"] = "hidden@platform.store"
            else:
                # Fallback if df_customers is completely empty or missing structural indexes
                detailed_report = shopper_frequency.copy()
                detailed_report["name"] = detailed_report["customer_id"].apply(lambda idx: f"Customer #{idx}")
                detailed_report["email"] = "hidden@platform.store"
                
            # Fill individual missing row values if the merge returned NaN for specific entries
            detailed_report["name"] = detailed_report["name"].fillna(
                detailed_report["customer_id"].apply(lambda idx: f"Customer #{idx}")
            )
            detailed_report["email"] = detailed_report["email"].fillna("hidden@platform.store")
                
            st.dataframe(
                detailed_report[["customer_id", "name", "email", "order_count", "total_spent", "Segment Group"]].rename(columns={
                    "customer_id": "Client Ref ID",
                    "name": "Customer Name",
                    "email": "Registered Email Address",
                    "order_count": "Total Checkouts",
                    "total_spent": "LTD Value ($)"
                }).sort_values(by="LTD Value ($)", ascending=False),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("⚠️ Insufficient customer dataset depth to execute clustering iterations. Acquire at least 4 unique client interactions to fit the K-Means matrix.")