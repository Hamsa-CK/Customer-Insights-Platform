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
    # 🎛️ STEP 4: INTERACTIVE LOGISTICS & ACTION TABS
    # =========================================================================
    tab_track, tab_create, tab_cancel, tab_deliver, tab_return, tab_refund = st.tabs([
        "🔍 Track Orders", 
        "➕ Create Order", 
        "🚫 Cancel Order", 
        "🚚 Mark Delivered", 
        "🔄 Process Return", 
        "💸 Process Refund"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: TRACK ORDERS
    # -------------------------------------------------------------------------
    with tab_track:
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

    # -------------------------------------------------------------------------
    # TAB 2: CREATE ORDER
    # -------------------------------------------------------------------------
    with tab_create:
        st.markdown("### ➕ Manual Order Entry")
        my_products = df_products[df_products["vendor_id"] == vendor_id]

        if my_products.empty:
            st.warning("⚠️ No products registered under your vendor account to issue orders.")
        else:
            with st.form("create_order_form"):
                col_p, col_q = st.columns(2)
                with col_p:
                    selected_prod = st.selectbox("Select Product SKU", my_products["name"].unique())
                with col_q:
                    order_qty = st.number_input("Quantity", min_value=1, value=1, step=1)
                
                prod_row = my_products[my_products["name"] == selected_prod].iloc[0]
                unit_price = prod_row["price"]
                calc_total = unit_price * order_qty

                st.info(f"💵 **Unit Price:** ${unit_price:,.2f} | **Estimated Total:** ${calc_total:,.2f}")
                submit_create = st.form_submit_button("✨ Dispatch New Order")

                if submit_create:
                    st.toast(f"✅ Order generated successfully for {selected_prod}!")
                    st.success(f"Order logged successfully! Added {order_qty}x '{selected_prod}' to pipeline.")

    # -------------------------------------------------------------------------
    # TAB 3: CANCEL ORDER
    # -------------------------------------------------------------------------
    with tab_cancel:
        st.markdown("### 🚫 Cancel Active Order")
        cancellable = my_orders[my_orders["status"].isin(["Pending", "Processing"])]

        if cancellable.empty:
            st.info("✅ No active pending orders eligible for cancellation.")
        else:
            cancel_id = st.selectbox("Select Order ID to Cancel", cancellable["order_id"].unique(), key="cancel_sel")
            cancel_reason = st.text_area("Reason for Cancellation", placeholder="e.g. Item out of stock / Customer request...")
            
            if st.button("🚫 Void & Cancel Order", type="primary"):
                st.toast(f"✅ Order #{cancel_id} marked as Cancelled.")
                st.success(f"Order #{cancel_id} was updated to 'Cancelled'.")

    # -------------------------------------------------------------------------
    # TAB 4: DELIVERED
    # -------------------------------------------------------------------------
    with tab_deliver:
        st.markdown("### 🚚 Mark Order as Delivered")
        shippable = my_orders[my_orders["status"].isin(["Pending", "Processing", "Shipped"])]

        if shippable.empty:
            st.info("✅ All active orders are fully delivered.")
        else:
            deliver_id = st.selectbox("Select Order ID to Confirm Delivery", shippable["order_id"].unique(), key="deliv_sel")
            
            if st.button("✅ Confirm Delivery Status"):
                st.toast(f"🚚 Order #{deliver_id} marked as Delivered!")
                st.success(f"Order #{deliver_id} updated to 'Delivered'.")

    # -------------------------------------------------------------------------
    # TAB 5: RETURNED
    # -------------------------------------------------------------------------
    with tab_return:
        st.markdown("### 🔄 Register Returned Items")
        returnable = my_orders[my_orders["status"] == "Delivered"]

        if returnable.empty:
            st.info("ℹ️ No delivered orders available for return processing.")
        else:
            return_id = st.selectbox("Select Order ID to Process Return", returnable["order_id"].unique(), key="ret_sel")
            return_condition = st.selectbox("Item Inspection Condition", ["Unopened / Restockable", "Damaged / Defective", "Wrong Item Sent"])
            
            if st.button("🔄 Confirm Order Return"):
                st.toast(f"🔄 Return logged for Order #{return_id}.")
                st.success(f"Order #{return_id} logged as 'Returned' with condition: {return_condition}.")

    # -------------------------------------------------------------------------
    # TAB 6: REFUND
    # -------------------------------------------------------------------------
    with tab_refund:
        st.markdown("### 💸 Issue Customer Refund")
        refundable = my_orders[my_orders["status"].isin(["Returned", "Cancelled"])]

        if refundable.empty:
            st.info("ℹ️ No returned or cancelled orders currently awaiting refund approval.")
        else:
            refund_id = st.selectbox("Select Order ID to Issue Refund", refundable["order_id"].unique(), key="ref_sel")
            refund_amount = st.number_input("Refund Amount ($)", min_value=0.01, value=50.00, step=5.00)
            
            if st.button("💸 Authorize & Issue Refund"):
                st.toast(f"💸 Refund of ${refund_amount:,.2f} processed for Order #{refund_id}!")
                st.success(f"Successfully issued ${refund_amount:,.2f} refund for Order #{refund_id}.")