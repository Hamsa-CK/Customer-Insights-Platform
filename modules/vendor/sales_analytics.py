import streamlit as st
import pandas as pd
import plotly.express as px

def show_sales_analytics(vendor_id, df_items, df_orders, df_products):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .analytics-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #3182ce;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            text-align: center;
        }
        .analytics-label {
            font-size: 0.8rem;
            color: #718096;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .analytics-value {
            font-size: 1.6rem;
            color: #1a202c;
            font-weight: 700;
            margin: 4px 0;
        }
        .analytics-footer {
            font-size: 0.75rem;
            color: #a0aec0;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("📊 Financial Intelligence & Trend Analytics")
    st.caption("Deep-dive exploration of margins, fulfillment metrics, and continuous distribution trends.")

    # =========================================================================
    # 🧮 STEP 1: ADVANCED FINANCIAL PROCESSING ENGINE
    # =========================================================================
    # Filter transactional items for this vendor
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy()
    
    if my_items.empty:
        st.info("📦 No transactional history found to calculate financial metrics yet.")
        return

    # Calculate item gross line metrics
    my_items["gross_line"] = my_items["quantity"] * my_items["price_per_unit"]
    
    # Merge items with products to get target baseline values for profit metrics
    my_items = pd.merge(my_items, df_products[["product_id", "name"]], on="product_id", how="left")
    
    # Cost modeling logic: base wholesale cost estimated at 65% of listing retail
    my_items["cost_basis_line"] = my_items["gross_line"] * 0.65
    my_items["profit_line"] = my_items["gross_line"] - my_items["cost_basis_line"]

    # Merge against main order registry for timelines and delivery statuses
    sales_master = pd.merge(my_items, df_orders[["order_id", "created_at", "status"]], on="order_id", how="inner")
    
    if sales_master.empty:
        st.info("⏳ Core transactional records are mapping. Check back shortly.")
        return

    # Date parse normalization
    sales_master["datetime"] = pd.to_datetime(sales_master["created_at"])
    sales_master["date"] = sales_master["datetime"].dt.date
    sales_master["month"] = sales_master["datetime"].dt.to_period("M").astype(str)

    # =========================================================================
    # 💰 STEP 2: KPI COMPILATION (GMV vs Net Sales Filters)
    # =========================================================================
    # ● GMV (Gross Merchandise Value): Every single logged dollar including cancellations
    gmv = sales_master["gross_line"].sum()

    # ● Net Revenue & Profit: Exclude canceled and failed orders to showcase actual earnings
    valid_sales = sales_master[~sales_master["status"].isin(["Cancelled", "Failed"])]
    revenue = valid_sales["gross_line"].sum()
    profit = valid_sales["profit_line"].sum()

    # ● Unique Orders Count & AOV (Average Order Value)
    total_orders_count = valid_sales["order_id"].nunique()
    aov = (revenue / total_orders_count) if total_orders_count > 0 else 0.0

    # Calculate time-series snapshots for the UI Cards
    latest_day = valid_sales.groupby("date")["gross_line"].sum().reset_index()
    daily_sales_value = latest_day.iloc[-1]["gross_line"] if not latest_day.empty else 0.0

    latest_month = valid_sales.groupby("month")["gross_line"].sum().reset_index()
    monthly_sales_value = latest_month.iloc[-1]["gross_line"] if not latest_month.empty else 0.0

    # =========================================================================
    # 🎛️ STEP 3: HIGH-FIDELITY UX KPI CARDS
    # =========================================================================
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    with row1_col1:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #2ecc71;">
                <div class="analytics-label">Net Revenue</div>
                <div class="analytics-value">${revenue:,.2f}</div>
                <div class="analytics-footer">Realized marketplace payout</div>
            </div>
        """, unsafe_allow_html=True)
    with row1_col2:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #3498db;">
                <div class="analytics-label">Gross GMV</div>
                <div class="analytics-value">${gmv:,.2f}</div>
                <div class="analytics-footer">Total value of all checkouts</div>
            </div>
        """, unsafe_allow_html=True)
    with row1_col3:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #e67e22;">
                <div class="analytics-label">Net Profit</div>
                <div class="analytics-value">${profit:,.2f}</div>
                <div class="analytics-footer">Estimated ~35% net margin</div>
            </div>
        """, unsafe_allow_html=True)
    with row1_col4:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #9b59b6;">
                <div class="analytics-label">Total Orders</div>
                <div class="analytics-value">{total_orders_count:,}</div>
                <div class="analytics-footer">Successful receipts processed</div>
            </div>
        """, unsafe_allow_html=True)

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #1abc9c; padding: 14px;">
                <div class="analytics-label">Daily Sales Run-Rate</div>
                <div class="analytics-value" style="font-size: 1.4rem;">${daily_sales_value:,.2f}</div>
                <div class="analytics-footer">Most recent operational day</div>
            </div>
        """, unsafe_allow_html=True)
    with row2_col2:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #34495e; padding: 14px;">
                <div class="analytics-label">Monthly Sales Run-Rate</div>
                <div class="analytics-value" style="font-size: 1.4rem;">${monthly_sales_value:,.2f}</div>
                <div class="analytics-footer">Current month total volume</div>
            </div>
        """, unsafe_allow_html=True)
    with row2_col3:
        st.markdown(f"""
            <div class="analytics-card" style="border-top-color: #e74c3c; padding: 14px;">
                <div class="analytics-label">Average Order Value</div>
                <div class="analytics-value" style="font-size: 1.4rem;">${aov:,.2f}</div>
                <div class="analytics-footer">Mean spending per checkout ticket</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 📊 STEP 4: CHARTS & INTELLIGENCE VISUALIZATIONS
    # =========================================================================
    chart_row1_col1, chart_row1_col2 = st.columns(2)

    with chart_row1_col1:
        # 📈 LINE CHART: Daily Sales
        st.markdown("#### 📈 Line Chart: Daily Sales Pipeline Velocity")
        daily_data = valid_sales.groupby("date")["gross_line"].sum().reset_index()
        fig_line = px.line(
            daily_data, x="date", y="gross_line",
            labels={"date": "Date", "gross_line": "Daily Sales ($)"},
            color_discrete_sequence=["#2ecc71"], markers=True
        )
        fig_line.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

    with chart_row1_col2:
        # 🌊 AREA CHART: Monthly Sales Trend
        st.markdown("#### 🌊 Area Chart: Monthly Performance Aggregations")
        monthly_data = valid_sales.groupby("month")["gross_line"].sum().reset_index()
        fig_area = px.area(
            monthly_data, x="month", y="gross_line",
            labels={"month": "Billing Month", "gross_line": "Sales Volume ($)"},
            color_discrete_sequence=["#3498db"]
        )
        fig_area.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_area, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    chart_row2_col1, chart_row2_col2 = st.columns(2)

    with chart_row2_col1:
        # 📊 BAR CHART: Product Revenue Split
        st.markdown("#### 📊 Bar Chart: Revenue Breakdown By SKU")
        prod_data = valid_sales.groupby("name")["gross_line"].sum().reset_index()
        prod_data = prod_data.sort_values(by="gross_line", ascending=True).tail(5) # Horizontal top 5
        
        fig_bar = px.bar(
            prod_data, x="gross_line", y="name", orientation="h",
            labels={"gross_line": "Revenue ($)", "name": "Product SKU"},
            color="gross_line", color_continuous_scale="Blues"
        )
        fig_bar.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_row2_col2:
        # 🍕 PIE CHART: Order Status Allocation
        st.markdown("#### 🍕 Pie Chart: Share of Order States")
        status_data = sales_master.groupby("status")["order_id"].count().reset_index()
        
        fig_pie = px.pie(
            status_data, values="order_id", names="status",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_pie, use_container_width=True)