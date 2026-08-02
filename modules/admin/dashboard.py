import pandas as pd
import plotly.express as px
import streamlit as st
from modules.ml_engine import predict_inventory_demand


def show_dashboard(df_products, df_orders, df_vendors, df_customers, df_items):
    # ==========================================
    # 🌟 PART 1: GLOBAL PERFORMANCE CARDS (GMV & Revenue)
    # ==========================================
    st.markdown(
        """
        <div style="background-color: #9370DB; padding: 20px 30px; border-radius: 0px; margin-left: -5rem; margin-right: -5rem; margin-top: -2rem; margin-bottom: 25px;">
            <h3 style="color: white; margin: 0; font-size: 32px;">📈 Global Platform Financials</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calculate real-time financial metrics directly from the loaded order database
    completed_orders = df_orders[df_orders["status"] != "Cancelled"]
    total_gmv = completed_orders["total_amount"].sum()
    platform_revenue = total_gmv * 0.10  # 10% platform commission

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
        <div style="background-color:#EBF5FB; padding:20px; border-radius:12px; border-left: 6px solid #2980B9; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="margin:0; font-size:14px; color:#566573; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px;">Gross Merchandise Value (GMV)</p>
            <h2 style="margin:5px 0 0 0; color:#2C3E50; font-size:32px;">${total_gmv:,.2f}</h2>
            <p style="margin:5px 0 0 0; font-size:12px; color:#7F8C8D;">Total gross sales calculated from non-cancelled transactions</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="background-color:#EAF2F8; padding:20px; border-radius:12px; border-left: 6px solid #1F618D; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <p style="margin:0; font-size:14px; color:#566573; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px;">Platform Revenue (10% Comm.)</p>
            <h2 style="margin:5px 0 0 0; color:#1F618D; font-size:32px;">${platform_revenue:,.2f}</h2>
            <p style="margin:5px 0 0 0; font-size:12px; color:#7F8C8D;">Admin earnings collected across platform transactions</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📊 PART 2: TOTAL COUNT WIDGETS
    # ==========================================
    st.markdown(
        """
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">🧮 Core Platform Metrics</h3>
        """,
        unsafe_allow_html=True,
    )

    # Exact counts from actual dataset entries
    total_vendors = int(df_vendors["vendor_id"].nunique())
    total_customers = int(df_customers["customer_id"].nunique())
    total_products = int(df_products["product_id"].nunique())
    total_orders = int(df_orders["order_id"].nunique())

    wc1, wc2, wc3, wc4 = st.columns(4)
    with wc1:
        st.markdown(
            f"""
        <div style="background-color:#F4ECF7; padding:15px; border-radius:8px; text-align:center; border-bottom: 4px solid #8E44AD;">
            <p style="margin:0; font-size:12px; color:#7D3C98; font-weight:bold;">ACTIVE VENDORS</p>
            <h3 style="margin:5px 0 0 0; color:#4A235A;">{total_vendors:,}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with wc2:
        st.markdown(
            f"""
        <div style="background-color:#E8F8F5; padding:15px; border-radius:8px; text-align:center; border-bottom: 4px solid #16A085;">
            <p style="margin:0; font-size:12px; color:#16A085; font-weight:bold;">TOTAL CUSTOMERS</p>
            <h3 style="margin:5px 0 0 0; color:#0E6251;">{total_customers:,}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with wc3:
        st.markdown(
            f"""
        <div style="background-color:#FEF9E7; padding:15px; border-radius:8px; text-align:center; border-bottom: 4px solid #F1C40F;">
            <p style="margin:0; font-size:12px; color:#B7950B; font-weight:bold;">LIVE PRODUCTS</p>
            <h3 style="margin:5px 0 0 0; color:#7D6608;">{total_products:,}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with wc4:
        st.markdown(
            f"""
        <div style="background-color:#FBEEE6; padding:15px; border-radius:8px; text-align:center; border-bottom: 4px solid #E67E22;">
            <p style="margin:0; font-size:12px; color:#E67E22; font-weight:bold;">ORDERS PLACED</p>
            <h3 style="margin:5px 0 0 0; color:#7E5109;">{total_orders:,}</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📈 PART 3: GRAPHS AND VISUALS
    # ==========================================
    st.markdown(
        """
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">🔍 Analytics & Forecasting Trends</h3>
        """,
        unsafe_allow_html=True,
    )

    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown("#### 📅 Dataset Sales Trend")
        # Build Monthly Sales directly from timestamps stored in the orders parquet file
        df_orders_trend = df_orders.copy()
        df_orders_trend["date"] = (
            pd.to_datetime(df_orders_trend["created_at"])
            .dt.to_period("M")
            .astype(str)
        )
        monthly_sales = (
            df_orders_trend.groupby("date")["total_amount"]
            .sum()
            .reset_index()
            .sort_values("date")
        )

        fig_trend = px.line(
            monthly_sales,
            x="date",
            y="total_amount",
            markers=True,
            labels={"total_amount": "Revenue ($)", "date": "Month"},
            color_discrete_sequence=["#1F618D"],
        )
        fig_trend.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300)
        st.plotly_chart(fig_trend, use_container_width=True)

    with g_col2:
        st.markdown("#### 🔮 30-Day Predictive Stock Demand Targets")
        # Calculate real inventory demand predictions straight from current datasets using our ML engine
        with st.spinner("Analyzing demand parameters..."):
            forecast_df = predict_inventory_demand().head(8).copy()

        fig_forecast = px.bar(
            forecast_df,
            x="product_name",
            y="predicted_required_stock",
            labels={
                "predicted_required_stock": "Target Stock Units",
                "product_name": "Product",
            },
            color="predicted_required_stock",
            color_continuous_scale="Viridis",
        )
        fig_forecast.update_layout(
            margin=dict(l=20, r=20, t=10, b=20),
            height=300,
            xaxis={"tickangle": -30, "title": None},
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 🏪 PART 4: TOP VENDORS & STOCK CHECKS
    # ==========================================
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown("#### 🏆 Top Performing Vendors (by Dataset Gross Revenue)")
        # Dynamically join transactional order items to registered active business profiles
        df_items_calc = df_items.copy()
        if "subtotal" in df_items_calc.columns:
            df_items_calc["gross_revenue"] = df_items_calc["subtotal"]
        else:
            df_items_calc["gross_revenue"] = (
                df_items_calc["quantity"] * df_items_calc["price_per_unit"]
            )

        vendor_sales = (
            df_items_calc.groupby("vendor_id")["gross_revenue"]
            .sum()
            .reset_index()
        )
        top_vendors = pd.merge(vendor_sales, df_vendors, on="vendor_id")
        top_vendors = top_vendors.sort_values(
            by="gross_revenue", ascending=False
        ).head(5)

        fig_vendors = px.bar(
            top_vendors,
            x="gross_revenue",
            y="business_name",
            orientation="h",
            labels={
                "gross_revenue": "Gross Sales ($)",
                "business_name": "Store Name",
            },
            color_discrete_sequence=["#2980B9"],
        )
        fig_vendors.update_layout(
            margin=dict(l=20, r=20, t=10, b=20),
            height=250,
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_vendors, use_container_width=True)

    with info_col2:
        st.markdown("#### ⚠️ Low Stock Alerts")
        # Direct threshold filter on current stock numbers from datasets
        low_stock_df = df_products[
            df_products["current_stock"] <= df_products["low_stock_threshold"]
        ].head(5)

        if not low_stock_df.empty:
            st.dataframe(
                low_stock_df[
                    [
                        "name",
                        "category",
                        "current_stock",
                        "low_stock_threshold",
                    ]
                ].rename(
                    columns={
                        "name": "Product",
                        "category": "Category",
                        "current_stock": "In Stock",
                        "low_stock_threshold": "Threshold",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success(
                "✅ All marketplace inventory meets target security safety thresholds."
            )