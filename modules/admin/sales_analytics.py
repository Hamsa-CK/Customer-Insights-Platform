import streamlit as st
import pandas as pd
import plotly.express as px

def show_sales_analytics(df_orders, df_items, df_products):
    st.subheader("💰 Platform Sales & Transaction Insights")
    
    # Defensive copies & empty checks
    df_orders = df_orders.copy() if df_orders is not None else pd.DataFrame()
    df_items = df_items.copy() if df_items is not None else pd.DataFrame()
    df_products = df_products.copy() if df_products is not None else pd.DataFrame()

    # Filter out cancelled orders for accurate financial metrics
    if not df_orders.empty and "status" in df_orders.columns:
        valid_orders = df_orders[df_orders["status"] != "Cancelled"].copy()
    else:
        valid_orders = df_orders.copy()

    if not valid_orders.empty and "created_at" in valid_orders.columns:
        valid_orders["created_at"] = pd.to_datetime(valid_orders["created_at"], errors="coerce")
    elif "created_at" not in valid_orders.columns:
        valid_orders["created_at"] = pd.NaT

    # Ensure items are matched with products to handle category analyses
    if not df_items.empty and not df_products.empty and "product_id" in df_items.columns and "product_id" in df_products.columns:
        df_merged_items = pd.merge(df_items, df_products, on="product_id", suffixes=('', '_prod'))
    else:
        df_merged_items = pd.DataFrame()

    # ==========================================
    # 🧮 PART 1: CORE SALES METRICS (KPIs)
    # ==========================================
    
    # Calculations
    gmv = valid_orders["total_amount"].sum() if not valid_orders.empty and "total_amount" in valid_orders.columns else 0.0
    platform_revenue = gmv * 0.10  # Platform commission earnings (10%)
    platform_profit = platform_revenue * 0.85  # Proxy: 85% of platform revenue is net profit
    total_orders = len(valid_orders)
    avg_order_value = gmv / total_orders if total_orders > 0 else 0.0

    # Layout Row 1: Revenue, GMV, Profit
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.markdown(f"""
        <div style="background-color:#EAF2F8; padding:20px; border-radius:10px; border-left: 5px solid #1F618D;">
            <p style="margin:0; font-size:13px; color:#566573; font-weight:bold; text-transform:uppercase;">Platform Revenue (10%)</p>
            <h2 style="margin:5px 0 0 0; color:#1F618D;">${platform_revenue:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""
        <div style="background-color:#EBF5FB; padding:20px; border-radius:10px; border-left: 5px solid #2980B9;">
            <p style="margin:0; font-size:13px; color:#566573; font-weight:bold; text-transform:uppercase;">Gross Merchandise Value (GMV)</p>
            <h2 style="margin:5px 0 0 0; color:#2C3E50;">${gmv:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"""
        <div style="background-color:#E8F8F5; padding:20px; border-radius:10px; border-left: 5px solid #16A085;">
            <p style="margin:0; font-size:13px; color:#566573; font-weight:bold; text-transform:uppercase;">Platform Net Profit</p>
            <h2 style="margin:5px 0 0 0; color:#16A085;">${platform_profit:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Layout Row 2: Orders, Average Order Value
    kpi_col4, kpi_col5 = st.columns(2)
    with kpi_col4:
        st.markdown(f"""
        <div style="background-color:#FDF2E9; padding:20px; border-radius:10px; border-left: 5px solid #E67E22;">
            <p style="margin:0; font-size:13px; color:#566573; font-weight:bold; text-transform:uppercase;">Total Volume Orders</p>
            <h2 style="margin:5px 0 0 0; color:#E67E22;">{total_orders:,}</h2>
        </div>
        """, unsafe_allow_html=True)
    with kpi_col5:
        st.markdown(f"""
        <div style="background-color:#F5EEF8; padding:20px; border-radius:10px; border-left: 5px solid #8E44AD;">
            <p style="margin:0; font-size:13px; color:#566573; font-weight:bold; text-transform:uppercase;">Average Order Value (AOV)</p>
            <h2 style="margin:5px 0 0 0; color:#8E44AD;">${avg_order_value:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ==========================================
    # 📊 PART 2: INTERACTIVE CHARTS
    # ==========================================
    
    chart_tab1, chart_tab2 = st.columns(2)
    
    with chart_tab1:
        # Chart 1: Daily Sales Trend (Line Chart)
        st.markdown("#### 📅 Daily Sales Revenue Trend")
        if not valid_orders.empty and "created_at" in valid_orders.columns and valid_orders["created_at"].notna().any() and "total_amount" in valid_orders.columns:
            valid_orders["day"] = valid_orders["created_at"].dt.date
            daily_sales = valid_orders.dropna(subset=["day"]).groupby("day")["total_amount"].sum().reset_index()
            
            if not daily_sales.empty:
                fig_line = px.line(
                    daily_sales,
                    x="day",
                    y="total_amount",
                    labels={"total_amount": "Sales Volume ($)", "day": "Date"},
                    color_discrete_sequence=["#2980B9"],
                    markers=True
                )
                fig_line.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No daily sales trends recorded.")
        else:
            st.info("No sales trend data available.")

    with chart_tab2:
        # Chart 2: Category Sales Share (Pie Chart)
        st.markdown("#### 🍕 Category Distribution (by Value)")
        if not df_merged_items.empty and "quantity" in df_merged_items.columns and "price_per_unit" in df_merged_items.columns and "category" in df_merged_items.columns:
            df_merged_items["total_value"] = df_merged_items["quantity"] * df_merged_items["price_per_unit"]
            cat_sales = df_merged_items.groupby("category")["total_value"].sum().reset_index()
            
            if not cat_sales.empty:
                fig_pie = px.pie(
                    cat_sales,
                    names="category",
                    values="total_value",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No category sales records found.")
        else:
            st.info("No item category data available.")

    st.markdown("<br>", unsafe_allow_html=True)

    chart_tab3, chart_tab4 = st.columns(2)

    with chart_tab3:
        # Chart 3: Monthly Growth (Bar Chart)
        st.markdown("#### 📊 Monthly Gross Order Volume")
        if not valid_orders.empty and "created_at" in valid_orders.columns and valid_orders["created_at"].notna().any() and "total_amount" in valid_orders.columns:
            valid_orders["month"] = valid_orders["created_at"].dt.to_period("M").astype(str)
            monthly_sales = valid_orders.dropna(subset=["month"]).groupby("month")["total_amount"].sum().reset_index().sort_values("month")
            
            if not monthly_sales.empty:
                fig_bar = px.bar(
                    monthly_sales,
                    x="month",
                    y="total_amount",
                    labels={"total_amount": "GMV ($)", "month": "Month"},
                    color_discrete_sequence=["#34495E"]
                )
                fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No monthly order volumes recorded.")
        else:
            st.info("No monthly sales data available.")

    with chart_tab4:
        # Chart 4: Cumulative Growth (Area Chart)
        st.markdown("#### 📈 Cumulative Platform GMV Over Time")
        if not valid_orders.empty and "created_at" in valid_orders.columns and valid_orders["created_at"].notna().any() and "total_amount" in valid_orders.columns:
            if "day" not in valid_orders.columns:
                valid_orders["day"] = valid_orders["created_at"].dt.date
            daily_sales_sorted = valid_orders.dropna(subset=["day"]).groupby("day")["total_amount"].sum().reset_index().sort_values("day")
            
            if not daily_sales_sorted.empty:
                daily_sales_sorted["cumulative_gmv"] = daily_sales_sorted["total_amount"].cumsum()
                
                fig_area = px.area(
                    daily_sales_sorted,
                    x="day",
                    y="cumulative_gmv",
                    labels={"cumulative_gmv": "Cumulative GMV ($)", "day": "Date"},
                    color_discrete_sequence=["#16A085"]
                )
                fig_area.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
                st.plotly_chart(fig_area, use_container_width=True)
            else:
                st.info("No cumulative growth records found.")
        else:
            st.info("No timeline data available for cumulative plot.")