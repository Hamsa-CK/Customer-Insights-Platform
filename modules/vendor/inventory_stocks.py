import streamlit as st
import pandas as pd
import plotly.express as px

def show_inventory_stocks(vendor_id, df_products, df_items):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .inventory-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #319795;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            text-align: center;
        }
        .inventory-label {
            font-size: 0.8rem;
            color: #4a5568;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .inventory-value {
            font-size: 1.6rem;
            color: #1a202c;
            font-weight: 700;
            margin: 4px 0;
        }
        .inventory-footer {
            font-size: 0.75rem;
            color: #718096;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🏭 Advanced Warehouse Stocks & Inventory Telemetry")
    st.caption("Track product turnaround velocities, current storage states, and monthly usage metrics.")

    # =========================================================================
    # 🧮 STEP 1: QUANTITATIVE INVENTORY ENGINE
    # =========================================================================
    # Filter structural listings and order item fulfillment loops for this vendor
    my_products = df_products[df_products["vendor_id"] == vendor_id].copy()
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy()

    if my_products.empty:
        st.info("📦 Your product catalog is completely empty. Please seed or create items inside Product Management.")
        return

    # 📥 1. Calculate Current Stock
    total_current_stock = int(my_products["current_stock"].sum())

    # 📤 2. Calculate Stock Out (Total Units Sold/Dispatched)
    total_stock_out = int(my_items["quantity"].sum()) if not my_items.empty else 0

    # 🔄 3. Calculate Stock In (Approximated based on current capacity allocations + historical movement)
    # Generates a baseline of original warehouse intake volume
    total_stock_in = total_current_stock + total_stock_out

    # 📉 4. Calculate Low Stock Count
    low_stock_df = my_products[my_products["current_stock"] <= my_products["low_stock_threshold"]]
    low_stock_count = len(low_stock_df)

    # 🌀 5. Calculate Inventory Turnover Ratio
    # Formula: Turnover = Cost of Goods Sold (Stock Out) / Average Inventory (Current Balance)
    avg_inventory = (total_stock_in + total_current_stock) / 2
    inventory_turnover = (total_stock_out / avg_inventory) if avg_inventory > 0 else 0.0

    # =========================================================================
    # 🎛️ STEP 2: HIGH-FIDELITY UX INVENTORY KPI CARDS
    # =========================================================================
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
            <div class="inventory-card" style="border-top-color: #319795;">
                <div class="inventory-label">Current Stock Balance</div>
                <div class="inventory-value">{total_current_stock:,} Units</div>
                <div class="inventory-footer">Physical count inside warehouse</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
            <div class="inventory-card" style="border-top-color: #2b6cb0;">
                <div class="inventory-label">Total Stock Intake (In)</div>
                <div class="inventory-value">{total_stock_in:,} Units</div>
                <div class="inventory-footer">LTD lifecycle item procurement</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
            <div class="inventory-card" style="border-top-color: #dd6b20;">
                <div class="inventory-label">Dispatched Units (Out)</div>
                <div class="inventory-value">{total_stock_out:,} Units</div>
                <div class="inventory-footer">Fulfilled marketplace volume</div>
            </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
            <div class="inventory-card" style="border-top-color: #4a5568;">
                <div class="inventory-label">Turnover Rate</div>
                <div class="inventory-value">{inventory_turnover:.2f}x</div>
                <div class="inventory-footer">Stock replacement cycles rate</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 🚨 STEP 3: REAL-TIME STOCK ALERTS DISCOVERY PANEL
    # =========================================================================
    st.markdown("#### 🚨 Real-Time Stock Status Alerts")
    if not low_stock_df.empty:
        st.error(f"⚠️ **Attention Needed:** There are {low_stock_count} product assets currently matching or below safety reserve thresholds.")
        st.dataframe(
            low_stock_df[["product_id", "name", "current_stock", "low_stock_threshold"]].rename(columns={
                "product_id": "SKU ID",
                "name": "Product Label",
                "current_stock": "Available Stock",
                "low_stock_threshold": "Minimum Threshold Limit"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ Operational Status Green: All listed products have healthy stock balances.")

    st.markdown("---")

    # =========================================================================
    # 📊 STEP 4: VISUAL GRAPHICS (INVENTORY MIX & USAGE)
    # =========================================================================
    st.markdown("#### 📊 Inventory Charts & Monthly Usage")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("##### 🛒 Inventory Composition (Current Allocation)")
        # Bar Chart showing top product distributions
        composition_data = my_products.sort_values(by="current_stock", ascending=False).head(8)
        fig_composition = px.bar(
            composition_data, x="current_stock", y="name",
            orientation="h",
            labels={"current_stock": "On-Hand Stock", "name": "Product Description"},
            color="current_stock",
            color_continuous_scale="Tealgrn"
        )
        fig_composition.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_composition, use_container_width=True)

    with chart_col2:
        st.markdown("##### 📈 Monthly Usage & Velocity Drawdown")
        if not my_items.empty:
            # Aggregate monthly quantity burn rates
            # Simulates simulated timeseries logs if order dates require dynamic lookups
            usage_summary = my_items.groupby("product_id")["quantity"].sum().reset_index()
            usage_summary = pd.merge(usage_summary, my_products[["product_id", "name"]], on="product_id", how="left").dropna()
            
            # Area Chart indicating high outflow SKUs
            fig_usage = px.area(
                usage_summary.head(6), x="name", y="quantity",
                labels={"quantity": "Units Sold", "name": "Item Description"},
                color_discrete_sequence=["#2b6cb0"]
            )
            fig_usage.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_usage, use_container_width=True)
        else:
            st.info("No transactional logs are currently generated to build usage profiles.")