import streamlit as st
import pandas as pd
import plotly.express as px

def show_payment_management(vendor_id, df_orders, df_items, df_payments=None, platform_fee_pct=0.10):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .pay-kpi-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
            text-align: center;
            margin-bottom: 15px;
        }
        .pay-kpi-label {
            font-size: 0.8rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .pay-kpi-val {
            font-size: 1.5rem;
            color: #0f172a;
            font-weight: 700;
            margin: 4px 0;
        }
        .pay-kpi-sub {
            font-size: 0.75rem;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("💳 Payment Intelligence & Settlement Hub")
    st.caption("Analyze payout distributions, gateway channel breakdown, and ledger records across all payment instruments.")

    # =========================================================================
    # 🧮 STEP 1: REAL DATASET PROCESSING ENGINE
    # =========================================================================
    # Filter transactional items for this vendor
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy() if "vendor_id" in df_items.columns else pd.DataFrame()

    if my_items.empty:
        st.info("ℹ️ No payment ledger history recorded for this vendor.")
        return

    # FIXED: Deduct platform fee (10%) to show net settled revenue
    my_items["gross_line"] = (my_items["quantity"] * my_items["price_per_unit"]) * (1.0 - platform_fee_pct)

    # Merge items with order registry for payment method & status tracking
    master_pay = pd.merge(my_items, df_orders, on="order_id", how="inner")

    if master_pay.empty:
        st.info("ℹ️ No matching order records found for vendor transactions.")
        return

    if "created_at" in master_pay.columns:
        master_pay["datetime"] = pd.to_datetime(master_pay["created_at"])
        master_pay["date"] = master_pay["datetime"].dt.date
    else:
        master_pay["date"] = "N/A"

    # Ensure standard payment methods exist in dataset
    if "payment_method" not in master_pay.columns:
        if df_payments is not None and "payment_method" in df_payments.columns:
            master_pay = pd.merge(master_pay, df_payments[["order_id", "payment_method"]], on="order_id", how="left")
        else:
            master_pay["payment_method"] = "UPI"

    master_pay["payment_method"] = master_pay["payment_method"].fillna("Other")

    # Standardize payment method strings (e.g. Map "COD" / "cod" / uppercase strings)
    master_pay["payment_method"] = master_pay["payment_method"].astype(str).str.strip().str.upper()
    master_pay["payment_method"] = master_pay["payment_method"].replace({
        "COD": "CASH",
        "CREDIT CARD": "CREDIT CARD",
        "NET BANKING": "NET BANKING"
    })

    # Filter out unpaid/cancelled checkouts for realized revenue calculations
    status_col = "status" if "status" in master_pay.columns else "status_x"
    if status_col in master_pay.columns:
        settled_pay = master_pay[~master_pay[status_col].isin(["Cancelled", "Failed"])]
    else:
        settled_pay = master_pay.copy()

    # Dynamic Payment Method Aggregations
    methods = ["CASH", "UPI", "CREDIT CARD", "DEBIT CARD", "NET BANKING", "WALLET"]
    method_totals = settled_pay.groupby("payment_method")["gross_line"].sum().to_dict()

    # =========================================================================
    # 💰 STEP 2: DYNAMIC DATASET KPI CARDS BY PAYMENT METHOD
    # =========================================================================
    total_realized_revenue = settled_pay["gross_line"].sum()
    
    st.markdown("### 🏛️ Method Settlement Overview")
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    method_cols = [kpi1, kpi2, kpi3, kpi4, kpi5, kpi6]
    method_colors = ["#10b981", "#6366f1", "#f59e0b", "#06b6d4", "#ec4899", "#8b5cf6"]

    for col, method, color in zip(method_cols, methods, method_colors):
        amt = method_totals.get(method, 0.0)
        share_pct = (amt / total_realized_revenue * 100) if total_realized_revenue > 0 else 0.0
        with col:
            st.markdown(f"""
                <div class="pay-kpi-card" style="border-top: 4px solid {color};">
                    <div class="pay-kpi-label">{method}</div>
                    <div class="pay-kpi-val">${amt:,.2f}</div>
                    <div class="pay-kpi-sub" style="color: {color};">{share_pct:.1f}% share</div>
                </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # 📈 STEP 3: HIGH-DENSITY VISUALIZATION DASHBOARD
    # =========================================================================
    st.subheader("📊 Gateway Volume & Channel Breakdown")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Pie chart: Share of payment methods
        pay_share_df = settled_pay.groupby("payment_method")["gross_line"].sum().reset_index()
        fig_pie = px.pie(
            pay_share_df, values="gross_line", names="payment_method",
            title="Revenue Share by Payment Channel",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_pie.update_layout(height=300, margin=dict(l=10, r=10, t=35, b=10), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_col2:
        # Bar chart: Transaction volume by payment method
        pay_count_df = master_pay.groupby("payment_method")["order_id"].nunique().reset_index()
        fig_bar = px.bar(
            pay_count_df, x="payment_method", y="order_id",
            labels={"payment_method": "Payment Method", "order_id": "Unique Checkout Count"},
            title="Checkout Frequency per Payment Channel",
            color="order_id",
            color_continuous_scale="Tealgrn"
        )
        fig_bar.update_layout(height=300, margin=dict(l=10, r=10, t=35, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # 🎛️ STEP 4: PAYMENT METHOD LEDGERS & SETTLEMENT TABS
    # =========================================================================
    tabs = st.tabs([f"💵 {m}" if m == "CASH" else f"📲 {m}" if m == "UPI" else f"💳 {m}" if "CARD" in m else f"🏦 {m}" if m == "NET BANKING" else f"👛 {m}" for m in methods])

    for tab, method in zip(tabs, methods):
        with tab:
            st.markdown(f"### 📋 {method} Settlement Ledger")
            
            method_df = master_pay[master_pay["payment_method"] == method]

            if method_df.empty:
                st.info(f"ℹ️ No transaction records logged using **{method}** yet.")
            else:
                if status_col in method_df.columns:
                    m_rev = method_df[~method_df[status_col].isin(["Cancelled", "Failed"])]["gross_line"].sum()
                else:
                    m_rev = method_df["gross_line"].sum()
                    
                m_txns = method_df["order_id"].nunique()

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Total Settled Revenue", f"${m_rev:,.2f}")
                with col_b:
                    st.metric("Total Transactions Logged", f"{m_txns:,}")

                # Display transactional dataset breakdown table
                st.markdown("#### Transaction Records")
                display_cols = ["order_id", "date", "quantity", "price_per_unit", "gross_line"]
                if status_col in method_df.columns:
                    display_cols.append(status_col)

                table_df = method_df[display_cols].rename(columns={
                    "order_id": "Order ID",
                    "date": "Date",
                    "quantity": "Units",
                    "price_per_unit": "Unit Price ($)",
                    "gross_line": "Total ($)",
                    status_col: "Order Status"
                })

                st.dataframe(
                    table_df,
                    use_container_width=True,
                    hide_index=True,
                    height=250
                )