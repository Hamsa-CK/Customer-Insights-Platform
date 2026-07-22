import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def show_churn_clv_analysis(df_customers, df_orders, df_items, df_products):
    st.subheader("🎯 Customer Retention, Churn Risk & Lifetime Value Model")

    # Safe Datetime Parsing
    df_orders = df_orders.copy()
    df_orders["created_at"] = pd.to_datetime(df_orders["created_at"])
    df_orders["Month"] = df_orders["created_at"].dt.to_period("M").astype(str)
    
    valid_orders = df_orders[df_orders["status"] != "Cancelled"]
    max_date = valid_orders["created_at"].max() if not valid_orders.empty else pd.Timestamp.now()

    # ==========================================
    # 🧠 ML FEATURE ENGINEERING: CLIENT PROFILE METRICS
    # ==========================================
    # Calculate Frequency and Lifetime Value (CLV) per customer
    customer_metrics = valid_orders.groupby("customer_id").agg(
        frequency=("order_id", "count"),
        clv=("total_amount", "sum"),
        last_purchase_date=("created_at", "max"),
        first_purchase_date=("created_at", "min")
    ).reset_index()

    # Calculate Recency (days since last purchase)
    customer_metrics["recency"] = (max_date - customer_metrics["last_purchase_date"]).dt.days

    # Map Churn Risk based on Recency Thresholds
    # Low Risk: < 30 days | Medium Risk: 30-60 days | High Risk: > 60 days
    def evaluate_churn_risk(recency):
        if recency <= 30:
            return "Low"
        elif recency <= 60:
            return "Medium"
        else:
            return "High"

    customer_metrics["churn_risk"] = customer_metrics["recency"].apply(evaluate_churn_risk)

    # Classify Customer CLV Value Tiers
    # High Value: Top 20% | Medium Value: Middle 60% | Low Value: Bottom 20%
    if not customer_metrics.empty:
        q_low = customer_metrics["clv"].quantile(0.20)
        q_high = customer_metrics["clv"].quantile(0.80)
    else:
        q_low, q_high = 0, 0

    def evaluate_clv_segment(clv_val):
        if clv_val >= q_high:
            return "High Value"
        elif clv_val >= q_low:
            return "Medium Value"
        else:
            return "Low Value"

    customer_metrics["clv_segment"] = customer_metrics["clv"].apply(evaluate_clv_segment)

    # Merge demographics back for full directory lookup
    full_metrics = pd.merge(df_customers, customer_metrics, on="customer_id", how="left")
    
    # Fill NaN values for customers with zero registered purchases
    full_metrics["clv"] = full_metrics["clv"].fillna(0.0)
    full_metrics["frequency"] = full_metrics["frequency"].fillna(0).astype(int)
    full_metrics["recency"] = full_metrics["recency"].fillna(180).astype(int)  # Assume inactive
    full_metrics["churn_risk"] = full_metrics["churn_risk"].fillna("High")
    full_metrics["clv_segment"] = full_metrics["clv_segment"].fillna("Low Value")

    # Add a fallback structural "ML Segment" for grouping (matches earlier module)
    def assign_ml_segment(row):
        if row["clv_segment"] == "High Value":
            return "Premium"
        elif row["frequency"] >= 3:
            return "Regular"
        elif row["frequency"] > 0:
            return "Occasional"
        else:
            return "Inactive"
    full_metrics["ml_segment"] = full_metrics.apply(assign_ml_segment, axis=1)

    # ==========================================
    # 🧮 PART 1: CORE METRICS (6 KPI Cards Required)
    # ==========================================
    st.markdown("### 📈 Churn & Value Lifecycle Health Indicators")
    
    total_cust = len(full_metrics)
    churn_at_risk = len(full_metrics[full_metrics["churn_risk"].isin(["Medium", "High"])])
    avg_clv_val = full_metrics["clv"].mean() if total_cust > 0 else 0.0
    high_value_cust = len(full_metrics[full_metrics["clv_segment"] == "High Value"])
    
    # Retention Rate
    returning_cust_count = len(full_metrics[full_metrics["frequency"] > 1])
    retention_rate = (returning_cust_count / total_cust * 100) if total_cust > 0 else 0.0
    
    # Predicted Churn Rate (Percentage of High Churn Risk users)
    high_risk_count = len(full_metrics[full_metrics["churn_risk"] == "High"])
    predicted_churn_rate = (high_risk_count / total_cust * 100) if total_cust > 0 else 0.0

    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        st.markdown(f"""
        <div style="background-color:#EBF5FB; padding:10px; border-radius:8px; border-bottom:3px solid #2980B9; text-align:center; min-height:120px;">
            <p style="margin:0; font-size:9px; color:#566573; font-weight:bold;">👥 TOTAL CUSTOMERS</p>
            <h3 style="margin:5px 0 0 0; color:#2C3E50; font-size:18px;">{total_cust:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[1]:
        st.markdown(f"""
        <div style="background-color:#FEF9E7; padding:10px; border-radius:8px; border-bottom:3px solid #F39C12; text-align:center; min-height:120px;">
            <p style="margin:0; font-size:9px; color:#566573; font-weight:bold;">⚠️ AT RISK OF CHURN</p>
            <h3 style="margin:5px 0 0 0; color:#7E5109; font-size:18px;">{churn_at_risk:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[2]:
        st.markdown(f"""
        <div style="background-color:#E8F8F5; padding:10px; border-radius:8px; border-bottom:3px solid #16A085; text-align:center; min-height:120px;">
            <p style="margin:0; font-size:9px; color:#566573; font-weight:bold;">💰 AVERAGE CLV</p>
            <h3 style="margin:5px 0 0 0; color:#0E6251; font-size:18px;">${avg_clv_val:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[3]:
        st.markdown(f"""
        <div style="background-color:#EBDEF0; padding:10px; border-radius:8px; border-bottom:3px solid #8E44AD; text-align:center; min-height:120px;">
            <p style="margin:0; font-size:9px; color:#566573; font-weight:bold;">⭐ HIGH-VALUE USERS</p>
            <h3 style="margin:5px 0 0 0; color:#4A235A; font-size:18px;">{high_value_cust:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[4]:
        st.markdown(f"""
        <div style="background-color:#EAF2F8; padding:10px; border-radius:8px; border-bottom:3px solid #3498DB; text-align:center; min-height:120px;">
            <p style="margin:0; font-size:9px; color:#566573; font-weight:bold;">🔄 RETENTION RATE</p>
            <h3 style="margin:5px 0 0 0; color:#1B4F72; font-size:18px;">{retention_rate:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_cols[5]:
        st.markdown(f"""
        <div style="background-color:#FDEDEC; padding:10px; border-radius:8px; border-bottom:3px solid #E74C3C; text-align:center; min-height:120px;">
            <p style="margin:0; font-size:9px; color:#566573; font-weight:bold;">📉 PREDICTED CHURN</p>
            <h3 style="margin:5px 0 0 0; color:#78281F; font-size:18px;">{predicted_churn_rate:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📊 PART 2: VISUALIZATIONS (10 Charts Required)
    # ==========================================
    st.markdown("### 📊 Predictive Cohorts & CLV Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Chart 1: Churn Risk Distribution – Donut Chart
        st.markdown("#### 1️⃣ Churn Risk Distribution Profile")
        risk_counts = full_metrics["churn_risk"].value_counts().reset_index()
        risk_counts.columns = ["Risk Category", "Customers"]
        fig1 = px.pie(risk_counts, names="Risk Category", values="Customers", hole=0.5,
                      color="Risk Category", color_discrete_map={"Low": "#2ECC71", "Medium": "#F1C40F", "High": "#E74C3C"})
        fig1.update_layout(
            margin=dict(l=10, r=10, t=10, b=50), 
            height=270, 
            legend=dict(orientation="h", y=-0.38, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Chart 3: Top 10 Customers by CLV – Horizontal Bar Chart
        st.markdown("#### 3️⃣ Top 10 Customers by Lifetime Value (CLV)")
        if "first_name" in full_metrics.columns and "last_name" in full_metrics.columns:
            full_metrics["display_name"] = full_metrics["first_name"] + " " + full_metrics["last_name"]
        else:
            full_metrics["display_name"] = "Customer ID: " + full_metrics["customer_id"].astype(str)
            
        top_clv = full_metrics.sort_values(by="clv", ascending=False).head(10)
        fig3 = px.bar(top_clv, x="clv", y="display_name", orientation="h",
                      labels={"clv": "Lifetime Spend ($)", "display_name": "Customer"},
                      color="clv", color_continuous_scale="Viridis")
        fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, coloraxis_showscale=False, yaxis={"categoryorder":"total ascending"})
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # Chart 2: Predicted Churn by Customer Segment – Bar Chart
        st.markdown("#### 2️⃣ Predicted Churn Rate by Segment")
        segment_churn = full_metrics.groupby("ml_segment").apply(
            lambda x: (x["churn_risk"] == "High").sum() / len(x) * 100
        ).reset_index()
        segment_churn.columns = ["Segment", "Churn Rate (%)"]
        fig2 = px.bar(segment_churn, x="Segment", y="Churn Rate (%)", color="Segment",
                      color_discrete_sequence=px.colors.qualitative.Safe)
        fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

        # Chart 4: CLV Distribution – Histogram
        st.markdown("#### 4️⃣ Complete Customer CLV Density Curve")
        active_clv = full_metrics[full_metrics["clv"] > 0]
        fig4 = px.histogram(active_clv, x="clv", nbins=30, labels={"clv": "Lifetime Purchase Value ($)"},
                            color_discrete_sequence=["#9B59B6"])
        fig4.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        # Chart 5: Monthly Churn Trend – Line Chart
        st.markdown("#### 5️⃣ Monthly Customer Churn Inactivity Trend")
        valid_orders["churn_trigger_month"] = (valid_orders["created_at"] + pd.Timedelta(days=30)).dt.to_period("M").astype(str)
        monthly_churn_raw = valid_orders.groupby("churn_trigger_month")["customer_id"].nunique().reset_index()
        monthly_churn_raw.columns = ["Month", "Projected Churned Count"]
        fig5 = px.line(monthly_churn_raw.tail(12), x="Month", y="Projected Churned Count", markers=True, color_discrete_sequence=["#E74C3C"])
        fig5.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
        st.plotly_chart(fig5, use_container_width=True)

        # Chart 7: Customer Segmentation by CLV – Donut Chart
        st.markdown("#### 7️⃣ Revenue Contribution Shares by CLV Tier")
        clv_tier_shares = full_metrics.groupby("clv_segment")["clv"].sum().reset_index()
        fig7 = px.pie(clv_tier_shares, names="clv_segment", values="clv", hole=0.5,
                      color="clv_segment", color_discrete_map={"High Value": "#27AE60", "Medium Value": "#2980B9", "Low Value": "#7F8C8D"})
        fig7.update_layout(
            margin=dict(l=10, r=10, t=10, b=50), 
            height=270, 
            legend=dict(orientation="h", y=-0.38, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig7, use_container_width=True)

    with col4:
        # Chart 6: Customer Retention vs Churn – Stacked Bar Chart
        st.markdown("#### 6️⃣ Retention vs Churn Cohort Breakdown")
        ret_churn_data = full_metrics.groupby("clv_segment")["churn_risk"].value_counts().unstack().fillna(0).reset_index()
        fig6 = px.bar(ret_churn_data, x="clv_segment", y=["Low", "Medium", "High"], 
                      labels={"value": "Total Customer Volume", "clv_segment": "Value Tier", "variable": "Churn Risk"},
                      color_discrete_map={"Low": "#2ECC71", "Medium": "#F1C40F", "High": "#E74C3C"}, barmode="stack")
        fig6.update_layout(
            margin=dict(l=10, r=10, t=10, b=50), 
            height=270, 
            legend=dict(orientation="h", y=-0.38, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig6, use_container_width=True)

        # Chart 8: Average CLV by Product Category – Bar Chart
        st.markdown("#### 8️⃣ Average Lifetime Value (CLV) by Category Interest")
        df_merged_items = pd.merge(df_items, df_products, on="product_id", how="inner")
        df_merged_full = pd.merge(df_merged_items, valid_orders, on="order_id", how="inner")
        
        cat_clv = df_merged_full.groupby(["category", "customer_id"])["total_amount"].sum().reset_index()
        avg_cat_clv = cat_clv.groupby("category")["total_amount"].mean().reset_index()
        avg_cat_clv.columns = ["Category", "Average CLV ($)"]
        
        fig8 = px.bar(avg_cat_clv, x="Category", y="Average CLV ($)", color="Category", color_discrete_sequence=px.colors.qualitative.Set2)
        fig8.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, showlegend=False)
        st.plotly_chart(fig8, use_container_width=True)

    st.markdown("---")
    col5, col6 = st.columns(2)

    with col5:
       # Chart 9: CLV vs Purchase Frequency – Scatter Plot
        st.markdown("#### 9️⃣ CLV vs Purchase Frequency Distribution Map")
        fig9 = px.scatter(full_metrics[full_metrics["clv"] > 0], x="frequency", y="clv", color="churn_risk",
                          labels={"frequency": "Lifetime Purchase Counts (Frequency)", "clv": "Customer Lifetime Value ($)"},
                          color_discrete_map={"Low": "#2ECC71", "Medium": "#F1C40F", "High": "#E74C3C"}, 
                          size="clv", 
                          size_max=30)  # <-- Fixed parameter name here
        fig9.update_layout(
            margin=dict(l=10, r=10, t=10, b=50), 
            height=270, 
            legend=dict(orientation="h", y=-0.38, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig9, use_container_width=True)

    with col6:
        # Chart 10: Customer Acquisition vs Churn Trend – Line Chart
        st.markdown("🔟 Monthly Customer Acquisition vs Churn Curve")
        acq_data = customer_metrics.groupby(customer_metrics["first_purchase_date"].dt.to_period("M").astype(str))["customer_id"].count().reset_index()
        acq_data.columns = ["Month", "Acquired Customers"]
        
        churn_data = customer_metrics[customer_metrics["churn_risk"] == "High"].groupby(
            (customer_metrics["last_purchase_date"] + pd.Timedelta(days=30)).dt.to_period("M").astype(str)
        )["customer_id"].count().reset_index()
        churn_data.columns = ["Month", "Churned Customers"]
        
        merged_trend = pd.merge(acq_data, churn_data, on="Month", how="outer").fillna(0).sort_values("Month").tail(12)
        fig10 = px.line(merged_trend, x="Month", y=["Acquired Customers", "Churned Customers"], markers=True,
                        color_discrete_map={"Acquired Customers": "#2ECC71", "Churned Customers": "#E74C3C"})
        fig10.update_layout(
            margin=dict(l=10, r=10, t=10, b=50), 
            height=270, 
            legend=dict(orientation="h", y=-0.38, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig10, use_container_width=True)