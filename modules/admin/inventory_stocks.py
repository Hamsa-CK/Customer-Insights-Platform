import streamlit as st
import pandas as pd
import plotly.express as px

def show_inventory_stocks(df_products, df_items, df_orders):
    st.subheader("🧱 Platform Stock Status Monitoring")

    # ==========================================
    # 🧮 PART 1: INVENTORY KPI CARDS
    # ==========================================
    st.markdown("### 📈 Core Supply Metrics")
    
    # Clean orders to get completed transaction frames
    valid_orders = df_orders[df_orders["status"] != "Cancelled"]
    valid_items = df_items[df_items["order_id"].isin(valid_orders["order_id"])]
    
    # Metric Calculations
    total_current_stock = df_products["current_stock"].sum()
    
    # Proxying "In" and "Out" from dynamic dataset trends
    total_stock_out = valid_items["quantity"].sum()  # Total units checked out via completed orders
    total_stock_in = total_current_stock + total_stock_out # Estimate total items ever supplied
    
    # Inventory Turnover Ratio = Cost of Goods Sold (or total stock sold) / Average Inventory (or current stock)
    avg_inventory = df_products["current_stock"].mean()
    inventory_turnover = (total_stock_out / avg_inventory) if avg_inventory > 0 else 0.0
    
    # Calculate Low Stock count using item thresholds
    low_stock_df = df_products[df_products["current_stock"] <= df_products["low_stock_threshold"]]
    low_stock_count = len(low_stock_df)

    # Layout KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background-color:#EBF5FB; padding:15px; border-radius:8px; border-bottom: 4px solid #2980B9; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">CURRENT STOCK</p>
            <h3 style="margin:5px 0 0 0; color:#2C3E50;">{total_current_stock:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div style="background-color:#E8F8F5; padding:15px; border-radius:8px; border-bottom: 4px solid #16A085; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">STOCK IN (EST.)</p>
            <h3 style="margin:5px 0 0 0; color:#0E6251;">{total_stock_in:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div style="background-color:#FDEDEC; padding:15px; border-radius:8px; border-bottom: 4px solid #E74C3C; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">STOCK OUT (SOLD)</p>
            <h3 style="margin:5px 0 0 0; color:#78281F;">{total_stock_out:,}</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div style="background-color:#FEF9E7; padding:15px; border-radius:8px; border-bottom: 4px solid #F1C40F; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">TURNOVER RATIO</p>
            <h3 style="margin:5px 0 0 0; color:#7D6608;">{inventory_turnover:.2f}x</h3>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        # Low Stock triggers a warning styling if count > 0
        bg_color = "#FDEDEC" if low_stock_count > 0 else "#EAF2F8"
        border_col = "#E74C3C" if low_stock_count > 0 else "#3498DB"
        text_col = "#78281F" if low_stock_count > 0 else "#1B4F72"
        
        st.markdown(f"""
        <div style="background-color:{bg_color}; padding:15px; border-radius:8px; border-bottom: 4px solid {border_col}; text-align:center;">
            <p style="margin:0; font-size:11px; color:#566573; font-weight:bold;">LOW STOCK WARNINGS</p>
            <h3 style="margin:5px 0 0 0; color:{text_col};">{low_stock_count}</h3>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 🚨 PART 2: CRITICAL LOW STOCK WARNING SYSTEM
    # ==========================================
    st.markdown("### 🚨 Depleted & Critical Safety Level Triggers")
    
    if not low_stock_df.empty:
        st.error(f"⚠️ There are **{len(low_stock_df)}** items below warehouse threshold limits! Please submit reorder requests.")
        st.dataframe(
            low_stock_df[["product_id", "name", "category", "current_stock", "low_stock_threshold"]].rename(
                columns={
                    "product_id": "Product ID",
                    "name": "Product Name",
                    "category": "Category",
                    "current_stock": "Current Warehouse Balance",
                    "low_stock_threshold": "Safety Threshold Balance"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ Excellent! All platform products are currently above structural safety limits.")

    st.markdown("---")

    # ==========================================
    # 📈 PART 3: INVENTORY CHARTS & USAGE ANALYSIS
    # ==========================================
    st.markdown("### 📊 Demand & Stock Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("#### 🍕 Current Warehouse Distribution by Category")
        cat_balance = df_products.groupby("category")["current_stock"].sum().reset_index()
        
        fig_stock_pie = px.pie(
            cat_balance,
            names="category",
            values="current_stock",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_stock_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig_stock_pie, use_container_width=True)
        
    with chart_col2:
        st.markdown("#### 📅 Monthly Stock Usage Trend (Units Checked Out)")
        # Merging orders timestamps to order items to build Monthly Unit Usage
        merged_usage = pd.merge(df_items, df_orders[["order_id", "created_at"]], on="order_id")
        merged_usage["Month"] = pd.to_datetime(merged_usage["created_at"]).dt.to_period("M").astype(str)
        monthly_usage = merged_usage.groupby("Month")["quantity"].sum().reset_index().sort_values("Month")
        
        fig_usage_line = px.area(
            monthly_usage,
            x="Month",
            y="quantity",
            labels={"quantity": "Units Dispatched / Sold", "Month": "Billing Month"},
            color_discrete_sequence=["#9B59B6"]
        )
        fig_usage_line.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
        st.plotly_chart(fig_usage_line, use_container_width=True)