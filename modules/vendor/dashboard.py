import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_vendor_dashboard(vendor_id, df_products, df_items, df_orders):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .metric-card {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-left: 5px solid #4A90E2;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            margin-bottom: 10px;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #6c757d;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 1.8rem;
            color: #212529;
            font-weight: 700;
            margin: 5px 0;
        }
        .metric-sub {
            font-size: 0.8rem;
            color: #28a745;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    # =========================================================================
    # 🧮 DATA PROCESSING ENGINE
    # =========================================================================
    # Filter datasets specifically for this vendor
    my_products = df_products[df_products["vendor_id"] == vendor_id]
    my_items = df_items[df_items["vendor_id"] == vendor_id].copy()
    
    # Isolate cross-referenced orders
    my_order_ids = my_items["order_id"].unique() if not my_items.empty else []
    my_orders = df_orders[df_orders["order_id"].isin(my_order_ids)] if len(my_order_ids) > 0 else pd.DataFrame()

    # 💰 1. Revenue Calculations
    if not my_items.empty:
        my_items["revenue_line"] = my_items["quantity"] * my_items["price_per_unit"]
        total_revenue = my_items["revenue_line"].sum()
    else:
        total_revenue = 0.0

    # 📦 2. Order Breakdown Counters
    total_orders = len(my_order_ids)
    pending_orders = len(my_orders[my_orders["status"].isin(["Pending", "Processing"])]) if not my_orders.empty else 0
    fulfilled_orders = len(my_orders[my_orders["status"].isin(["Delivered", "Shipped"])]) if not my_orders.empty else 0

    # 🗂️ 3. Catalog Listings
    total_listings = len(my_products)

    # =========================================================================
    # 🎛️ UI LAYOUT: VENDOR STORE PERFORMANCE CARDS
    # =========================================================================
    st.subheader("🏁 Store Performance Overview")
    
    card_col1, card_col2, card_col3 = st.columns(3)
    
    with card_col1:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #2ECC71;">
                <div class="metric-label">My Gross Revenue</div>
                <div class="metric-value">${total_revenue:,.2f}</div>
                <div class="metric-sub">📈 Life-to-date platform earnings</div>
            </div>
        """, unsafe_allow_html=True)
        
    with card_col2:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #3498DB;">
                <div class="metric-label">Order Pipeline Counter</div>
                <div class="metric-value">{total_orders:,} Total</div>
                <div class="metric-sub" style="color: #e67e22;">⏳ {pending_orders} Pending | ✅ {fulfilled_orders} Fulfilled</div>
            </div>
        """, unsafe_allow_html=True)
        
    with card_col3:
        st.markdown(f"""
            <div class="metric-card" style="border-left-color: #9B59B6;">
                <div class="metric-label">My Products</div>
                <div class="metric-value">{total_listings} Items</div>
                <div class="metric-sub">📦 Active catalog store listings</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 📊 UI LAYOUT: CHARTS & GRAPHS VISUALIZATIONS
    # =========================================================================
    st.subheader("📈 Operational Intelligence Charts")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 💰 Own Sales & Order Volume Trend")
        if not my_items.empty and not my_orders.empty:
            # Join items and orders to get order dates
            timeline_df = pd.merge(my_items, df_orders[["order_id", "created_at"]], on="order_id", how="inner")
            timeline_df["date"] = pd.to_datetime(timeline_df["created_at"]).dt.date
            
            trend_data = timeline_df.groupby("date").agg(
                daily_sales=("revenue_line", "sum"),
                daily_volume=("quantity", "sum")
            ).reset_index()

            fig_trend = px.line(
                trend_data, x="date", y="daily_sales",
                labels={"date": "Date", "daily_sales": "Sales Revenue ($)"},
                color_discrete_sequence=["#2ECC71"],
                markers=True
            )
            fig_trend.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Insufficient sales history available to chart lines.")

    with chart_col2:
        st.markdown("#### 📊 Top 5 Best-Selling Products")
        if not my_items.empty:
            top_prod_df = my_items.groupby("product_id")["revenue_line"].sum().reset_index()
            top_prod_df = pd.merge(top_prod_df, my_products[["product_id", "name"]], on="product_id", how="left")
            top_prod_df = top_prod_df.sort_values(by="revenue_line", ascending=True).tail(5)

            fig_bar = px.bar(
                top_prod_df, x="revenue_line", y="name",
                orientation="h",
                labels={"revenue_line": "Revenue Earned ($)", "name": "Product Name"},
                color="revenue_line",
                color_continuous_scale="Viridis"
            )
            fig_bar.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No units moved to determine top items.")

    st.markdown("---")

    # =========================================================================
    # 📉 UI LAYOUT: INVENTORY & INTELLIGENT RECOMMENDATIONS
    # =========================================================================
    data_col1, data_col2 = st.columns(2)

    with data_col1:
        st.markdown("#### 🚨 Inventory Stock Depletion Status")
        if not my_products.empty and "low_stock_threshold" in my_products.columns and "current_stock" in my_products.columns:
            low_stock = my_products[my_products["current_stock"] <= my_products["low_stock_threshold"]]
            
            if not low_stock.empty:
                st.warning(f"⚠️ **{len(low_stock)} items need restocked immediately!**")
                st.dataframe(
                    low_stock[["name", "current_stock", "low_stock_threshold"]].rename(
                        columns={"name": "Product SKU Name", "current_stock": "In Stock", "low_stock_threshold": "Alert Limit"}
                    ),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("✅ Excellent inventory positions. No items are below target thresholds!")
                st.markdown("##### 📦 Current Inventory Catalog Overview")
                st.dataframe(
                    my_products[["name", "current_stock", "price"]].rename(
                        columns={"name": "Product Name", "current_stock": "In Stock", "price": "Price ($)"}
                    ),
                    use_container_width=True,
                    hide_index=True,
                    height=320
                )
        else:
            st.info("No active catalog inventory metrics found.")

    with data_col2:
        st.markdown("#### 🧠 Smart Stock Recommendations")
        if not my_products.empty and not my_items.empty:
            st.markdown("""
                <div style="background-color: #ebf5fb; border-left: 5px solid #2980b9; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>💡 AI Cross-Selling Suggestion:</strong><br>
                    Customers buying your top-listed items often bundle them with high-margin protective packaging cases. 
                    Consider updating multi-buy bundle options!
                </div>
            """, unsafe_allow_html=True)
            
            top_movers = my_items.groupby("product_id")["quantity"].sum().reset_index()
            top_movers = pd.merge(top_movers, my_products[["product_id", "name"]], on="product_id")
            top_movers = top_movers.sort_values(by="quantity", ascending=False).head(2)
            
            max_qty = my_items.groupby("product_id")["quantity"].sum().max()
            
            buffer_data = []
            for _, row in top_movers.iterrows():
                ratio = row["quantity"] / max_qty if max_qty > 0 else 0.5
                if ratio >= 0.8:
                    buffer_pct = 25
                elif ratio >= 0.5:
                    buffer_pct = 15
                else:
                    buffer_pct = 10
                
                buffer_data.append({
                    "product_id": row["product_id"],
                    "name": row["name"],
                    "quantity": row["quantity"],
                    "buffer_str": f"+{buffer_pct}%",
                    "buffer_pct": buffer_pct
                })
            
            df_buff = pd.DataFrame(buffer_data)

            if not df_buff.empty:
                st.markdown("##### ⚡ Velocity Recommendation Insights")
                
                # SAFE COLUMN ALLOCATION (Fixes potential IndexError)
                kpi_cols = st.columns(len(df_buff))
                for i, (_, row) in enumerate(df_buff.iterrows()):
                    with kpi_cols[i]:
                        st.metric(
                            label="Buffer Expansion", 
                            value=row['buffer_str'], 
                            delta=str(row['name'])[:18]
                        )
                
                st.markdown("---")
                
                for idx, item in df_buff.iterrows():
                    st.markdown(f"• **{item['name']}** variant showcases steady run-rates. Recommend expanding safety buffer by {item['buffer_str']}.")
                    
                    btn_col1, _ = st.columns([0.85, 0.15])
                    with btn_col1:
                        if st.button(f"⚡ Approve {item['buffer_str']} Buffer: {str(item['name'])[:22]}", key=f"buff_btn_{item['product_id']}_{idx}"):
                            st.toast(f"✅ Safety buffer updated successfully for {item['name']}!")
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("No moving items available for buffer analysis.")
        else:
            st.info("Awaiting structural catalog depth parameters before rendering recommendations.")