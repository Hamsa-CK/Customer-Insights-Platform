import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def show_order_management(vendor_id, df_orders, df_items, df_products):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .order-kpi-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
            text-align: center;
            margin-bottom: 15px;
        }
        .order-kpi-label {
            font-size: 0.8rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .order-kpi-val {
            font-size: 1.6rem;
            color: #0f172a;
            font-weight: 700;
            margin: 4px 0;
        }
        .order-kpi-sub {
            font-size: 0.75rem;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📦 Order Management & Logistics Engine")
    st.caption("Manage end-to-end customer order life cycles, process refunds/returns, and inspect real-time line items.")

    # =========================================================================
    # 🧮 STEP 1: REAL DATASET PROCESSING & FILTERING
    # =========================================================================
    # Isolate vendor items and cross-reference with order registry
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy()

    if my_items.empty:
        st.info("ℹ️ No operational order logs found for this vendor.")
        return

    my_order_ids = my_items["order_id"].unique()
    my_orders = df_orders[df_orders["order_id"].isin(my_order_ids)].copy()

    if my_orders.empty:
        st.info("ℹ️ No associated order details found for vendor items.")
        return

    # Calculate item gross line values
    if "price_per_unit" in my_items.columns and "quantity" in my_items.columns:
        my_items["line_total"] = my_items["quantity"] * my_items["price_per_unit"]

    # Merge items and orders for master analytics dataframe
    master_df = pd.merge(my_items, my_orders[["order_id", "created_at", "status"]], on="order_id", how="inner")
    master_df["created_at"] = pd.to_datetime(master_df["created_at"])
    master_df["date"] = master_df["created_at"].dt.date

    # =========================================================================
    # 📊 STEP 2: DYNAMIC DATASET-BASED KPI CARDS
    # =========================================================================
    total_orders = len(my_orders)
    pending_cnt = len(my_orders[my_orders["status"].isin(["Pending", "Processing"])])
    delivered_cnt = len(my_orders[my_orders["status"] == "Delivered"])
    returned_cnt = len(my_orders[my_orders["status"] == "Returned"])
    refunded_cnt = len(my_orders[my_orders["status"] == "Refunded"])
    cancelled_cnt = len(my_orders[my_orders["status"] == "Cancelled"])

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        st.markdown(f"""
            <div class="order-kpi-card" style="border-top: 4px solid #3b82f6;">
                <div class="order-kpi-label">Total Pipeline</div>
                <div class="order-kpi-val">{total_orders:,}</div>
                <div class="order-kpi-sub" style="color: #3b82f6;">📦 All Registered Orders</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
            <div class="order-kpi-card" style="border-top: 4px solid #f59e0b;">
                <div class="order-kpi-label">Active / Pending</div>
                <div class="order-kpi-val">{pending_cnt:,}</div>
                <div class="order-kpi-sub" style="color: #f59e0b;">⏳ Needs Action</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
            <div class="order-kpi-card" style="border-top: 4px solid #10b981;">
                <div class="order-kpi-label">Delivered</div>
                <div class="order-kpi-val">{delivered_cnt:,}</div>
                <div class="order-kpi-sub" style="color: #10b981;">✅ Completed Orders</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
            <div class="order-kpi-card" style="border-top: 4px solid #8b5cf6;">
                <div class="order-kpi-label">Returned / Refunded</div>
                <div class="order-kpi-val">{returned_cnt + refunded_cnt:,}</div>
                <div class="order-kpi-sub" style="color: #8b5cf6;">🔄 Reverse Logistics</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi5:
        st.markdown(f"""
            <div class="order-kpi-card" style="border-top: 4px solid #ef4444;">
                <div class="order-kpi-label">Cancelled</div>
                <div class="order-kpi-val">{cancelled_cnt:,}</div>
                <div class="order-kpi-sub" style="color: #ef4444;">🚫 Void Checkouts</div>
            </div>
        """, unsafe_allow_html=True)

    # =========================================================================
    # 📈 STEP 3: ANALYTICS VISUALIZATIONS (Plotly Graphs)
    # =========================================================================
    st.subheader("📈 Order Velocity & Status Distributions")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Timeline order volume plot
        daily_orders = master_df.groupby("date")["order_id"].nunique().reset_index()
        fig_line = px.line(
            daily_orders, x="date", y="order_id",
            labels={"date": "Order Date", "order_id": "Orders Placed"},
            title="Daily Order Fulfillment Trajectory",
            color_discrete_sequence=["#2563eb"], markers=True
        )
        fig_line.update_layout(height=280, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

    with chart_col2:
        # Status distribution pie chart
        status_df = my_orders.groupby("status")["order_id"].count().reset_index()
        fig_pie = px.pie(
            status_df, values="order_id", names="status",
            title="Order Status Breakdown",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=35, b=10), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # 🎛️ STEP 4: LOGISTICS TRACKING
    # =========================================================================

    # -------------------------------------------------------------------------
    # TRACK ORDERS
    # -------------------------------------------------------------------------
    st.markdown("### 🔍 Search & Track Order Status")

    col_search, col_filter = st.columns([0.7, 0.3])
    with col_search:
        search_query = st.text_input("🔎 Search by Order ID", placeholder="Type Order ID...")
    with col_filter:
        status_filter = st.selectbox("Filter Status", ["All"] + list(my_orders["status"].unique()))

    # Filter order table
    display_orders = my_orders.copy()
    if status_filter != "All":
        display_orders = display_orders[display_orders["status"] == status_filter]
        
    if search_query:
        display_orders = display_orders[display_orders["order_id"].astype(str).str.contains(search_query, case=False, regex=False)]

    st.dataframe(
        display_orders.rename(columns={
            "order_id": "Order ID", 
            "created_at": "Timestamp", 
            "status": "Fulfillment Status"
        }),
        use_container_width=True,
        hide_index=True,
        height=300
    )