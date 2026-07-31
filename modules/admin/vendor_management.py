import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- FIXED LINE: Point to modules.generator where the seeding function actually lives ---
try:
    from modules.generator import seed_vendor_marketplace_data
except ImportError:
    # Fallback to prevent app crashes if names vary locally
    try:
        from modules.data_seeder import seed_vendor_marketplace_data
    except ImportError:
        seed_vendor_marketplace_data = None

def show_vendor_management(df_vendors, df_items, df_orders, df_reviews=None):
    st.subheader("🛡️ Vendor Registrations & Gatekeeping")
    
    # Defensive copies & empty checks
    df_vendors = df_vendors.copy() if df_vendors is not None else pd.DataFrame()
    df_items = df_items.copy() if df_items is not None else pd.DataFrame()
    df_orders = df_orders.copy() if df_orders is not None else pd.DataFrame()
    df_reviews = df_reviews.copy() if df_reviews is not None else None

    if "status" not in df_vendors.columns:
        df_vendors["status"] = "Active"

    # ==========================================
    # 📋 PART 1: PENDING VENDORS APPLICATIONS
    # ==========================================
    st.markdown("### 📥 Pending Registrations Queue")
    pending_vendors = df_vendors[df_vendors["status"] == "Pending"]
    
    if not pending_vendors.empty and "business_name" in pending_vendors.columns:
        # Ensure standard columns exist
        for col in ["vendor_id", "business_name", "owner_name", "gst_number", "city", "state"]:
            if col not in pending_vendors.columns:
                pending_vendors[col] = "N/A"

        st.dataframe(
            pending_vendors[["vendor_id", "business_name", "owner_name", "gst_number", "city", "state"]].rename(
                columns={
                    "vendor_id": "ID",
                    "business_name": "Store/Shop Name",
                    "owner_name": "Applicant Name",
                    "gst_number": "GST/Tax ID",
                    "city": "City",
                    "state": "State"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("##### ⚡ Quick Approvals & Suspensions Controls")
        select_col, btn_col1, btn_col2 = st.columns([2, 1, 1])
        
        with select_col:
            pending_names = pending_vendors["business_name"].dropna().tolist()
            if pending_names:
                selected_vendor_name = st.selectbox(
                    "Select Vendor to Action", 
                    options=pending_names,
                    key="pending_select"
                )
                selected_row = pending_vendors[pending_vendors["business_name"] == selected_vendor_name].iloc[0]
                selected_id = selected_row["vendor_id"]
            else:
                selected_vendor_name = None
                selected_id = None
            
        if selected_id is not None:
            with btn_col1:
                if st.button("🟢 Approve Account", use_container_width=True, key=f"app_btn_{selected_id}"):
                    # 1. Update status to Active
                    df_vendors.loc[df_vendors["vendor_id"] == selected_id, "status"] = "Active"
                    os.makedirs("data", exist_ok=True)
                    try:
                        df_vendors.to_parquet("data/vendors.parquet", index=False)
                    except Exception as e:
                        st.error(f"Could not update status: {e}")
                    
                    # 2. Run the data generator utility safely
                    if seed_vendor_marketplace_data is not None:
                        try:
                            seed_vendor_marketplace_data(int(selected_id))
                            st.success(f"🎉 Approved {selected_vendor_name}! Marketplace metrics and histories linked successfully.")
                        except Exception as e:
                            st.warning(f"Approved account status, but historical data generation failed: {str(e)}")
                    else:
                        st.success(f"🎉 Approved {selected_vendor_name}!")
                    
                    st.rerun()
                    
            with btn_col2:
                if st.button("🔴 Reject / Suspend", use_container_width=True, key=f"susp_btn_{selected_id}"):
                    df_vendors.loc[df_vendors["vendor_id"] == selected_id, "status"] = "Suspended"
                    os.makedirs("data", exist_ok=True)
                    try:
                        df_vendors.to_parquet("data/vendors.parquet", index=False)
                    except Exception as e:
                        st.error(f"Could not update status: {e}")
                    st.warning(f"🚫 Suspended application for {selected_vendor_name}.")
                    st.rerun()
    else:
        st.info("🎉 There are currently no pending vendor registrations in the queue.")

    st.markdown("---")

    # ==========================================
    # 🗃️ PART 2: ALL REGISTERED VENDORS LIST
    # ==========================================
    st.markdown("### 🏬 Active & Suspended Sellers Directory")
    
    non_pending_vendors = df_vendors[df_vendors["status"] != "Pending"]
    
    if not non_pending_vendors.empty and "business_name" in non_pending_vendors.columns:
        for col in ["vendor_id", "business_name", "owner_name", "gst_number", "status"]:
            if col not in non_pending_vendors.columns:
                non_pending_vendors[col] = "N/A"

        st.dataframe(
            non_pending_vendors[["vendor_id", "business_name", "owner_name", "gst_number", "status"]].rename(
                columns={
                    "vendor_id": "Vendor ID",
                    "business_name": "Store/Shop Name",
                    "owner_name": "Owner Name",
                    "gst_number": "GST Number",
                    "status": "Current Status"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("##### ⚙️ Quick Status Modification Control")
        mod_col1, mod_col2 = st.columns([3, 1])
        
        with mod_col1:
            seller_names = non_pending_vendors["business_name"].dropna().tolist()
            if seller_names:
                selected_mod_name = st.selectbox(
                    "Select Seller Profile to Modify", 
                    options=seller_names,
                    key="mod_select"
                )
                mod_row = non_pending_vendors[non_pending_vendors["business_name"] == selected_mod_name].iloc[0]
                mod_id = mod_row["vendor_id"]
                current_status = mod_row["status"]
            else:
                selected_mod_name = None
                mod_id = None
                current_status = None
            
        if mod_id is not None:
            with mod_col2:
                if current_status == "Active":
                    if st.button("🔴 Suspend Seller", use_container_width=True, key=f"dir_susp_{mod_id}"):
                        df_vendors.loc[df_vendors["vendor_id"] == mod_id, "status"] = "Suspended"
                        os.makedirs("data", exist_ok=True)
                        try:
                            df_vendors.to_parquet("data/vendors.parquet", index=False)
                        except Exception as e:
                            st.error(f"Could not update status: {e}")
                        st.warning(f"🚫 Suspended access privileges for {selected_mod_name}.")
                        st.rerun()
                else:  # Suspended
                    if st.button("🟢 Activate Seller", use_container_width=True, key=f"dir_act_{mod_id}"):
                        df_vendors.loc[df_vendors["vendor_id"] == mod_id, "status"] = "Active"
                        os.makedirs("data", exist_ok=True)
                        try:
                            df_vendors.to_parquet("data/vendors.parquet", index=False)
                        except Exception as e:
                            st.error(f"Could not update status: {e}")
                        st.success(f"🟢 Reactivated marketplace status for {selected_mod_name}.")
                        st.rerun()
    else:
        st.info("No approved profiles created on the system yet.")

    st.markdown("---")

    # ==========================================
    # 🏆 PART 3: DATA CALCULATIONS & LEADERBOARD
    # ==========================================
    st.markdown("### 🏆 Platform Vendor Leaderboard")
    st.caption("Rankings calculated from transactional datasets, return tracking, and buyer reviews")

    if not df_items.empty and "vendor_id" in df_items.columns and "price_per_unit" in df_items.columns:
        rev_calc = df_items.groupby("vendor_id")["price_per_unit"].sum().reset_index()
        rev_calc.columns = ["vendor_id", "total_revenue"]
    else:
        rev_calc = pd.DataFrame(columns=["vendor_id", "total_revenue"])

    if df_reviews is None or df_reviews.empty:
        if os.path.exists("data/reviews.parquet"):
            try:
                df_reviews = pd.read_parquet("data/reviews.parquet")
            except Exception:
                df_reviews = pd.DataFrame(columns=["product_id", "rating"])
        else:
            df_reviews = pd.DataFrame(columns=["product_id", "rating"])

    if os.path.exists("data/products.parquet"):
        try:
            df_products = pd.read_parquet("data/products.parquet")
        except Exception:
            df_products = pd.DataFrame(columns=["product_id", "vendor_id"])
    else:
        df_products = pd.DataFrame(columns=["product_id", "vendor_id"])
    
    if not df_reviews.empty and "product_id" in df_reviews.columns and not df_products.empty and "product_id" in df_products.columns:
        reviews_merged = pd.merge(df_reviews, df_products, on="product_id")
        if not reviews_merged.empty and "vendor_id" in reviews_merged.columns and "rating" in reviews_merged.columns:
            ratings_calc = reviews_merged.groupby("vendor_id")["rating"].mean().reset_index()
            ratings_calc.columns = ["vendor_id", "avg_rating"]
        else:
            ratings_calc = pd.DataFrame(columns=["vendor_id", "avg_rating"])
    else:
        ratings_calc = pd.DataFrame(columns=["vendor_id", "avg_rating"])

    if not df_items.empty and not df_orders.empty and "order_id" in df_items.columns and "order_id" in df_orders.columns:
        items_orders_merged = pd.merge(df_items, df_orders, on="order_id")
    else:
        items_orders_merged = pd.DataFrame()
    
    if not items_orders_merged.empty and "vendor_id" in items_orders_merged.columns and "status" in items_orders_merged.columns:
        fulfillment_calc = items_orders_merged.groupby("vendor_id").apply(
            lambda x: (x["status"] == "Delivered").sum() / len(x) * 100
        ).reset_index(name="fulfillment_rate")

        refund_calc = items_orders_merged.groupby("vendor_id").apply(
            lambda x: (x["status"].isin(["Returned", "Refunded"])).sum() / len(x) * 100
        ).reset_index(name="refund_rate")
    else:
        fulfillment_calc = pd.DataFrame(columns=["vendor_id", "fulfillment_rate"])
        refund_calc = pd.DataFrame(columns=["vendor_id", "refund_rate"])

    if not df_vendors.empty and "vendor_id" in df_vendors.columns:
        leaderboard = df_vendors[df_vendors["status"] == "Active"].copy()
        leaderboard = pd.merge(leaderboard, rev_calc, on="vendor_id", how="left")
        leaderboard = pd.merge(leaderboard, ratings_calc, on="vendor_id", how="left")
        leaderboard = pd.merge(leaderboard, fulfillment_calc, on="vendor_id", how="left")
        leaderboard = pd.merge(leaderboard, refund_calc, on="vendor_id", how="left")

        if "total_revenue" not in leaderboard.columns:
            leaderboard["total_revenue"] = 0.0
        else:
            leaderboard["total_revenue"] = leaderboard["total_revenue"].fillna(0.0)

        if "avg_rating" not in leaderboard.columns:
            leaderboard["avg_rating"] = 4.5
        else:
            leaderboard["avg_rating"] = leaderboard["avg_rating"].fillna(4.5)

        if "fulfillment_rate" not in leaderboard.columns:
            leaderboard["fulfillment_rate"] = 95.0
        else:
            leaderboard["fulfillment_rate"] = leaderboard["fulfillment_rate"].fillna(95.0)

        if "refund_rate" not in leaderboard.columns:
            leaderboard["refund_rate"] = 0.0
        else:
            leaderboard["refund_rate"] = leaderboard["refund_rate"].fillna(0.0)

        leaderboard = leaderboard.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
        leaderboard.index += 1

        for col in ["business_name", "owner_name"]:
            if col not in leaderboard.columns:
                leaderboard[col] = "N/A"

        st.dataframe(
            leaderboard[["business_name", "owner_name", "total_revenue", "avg_rating", "fulfillment_rate", "refund_rate"]].rename(
                columns={
                    "business_name": "Store/Shop Name",
                    "owner_name": "Owner Name",
                    "total_revenue": "Total Sales Revenue ($)",
                    "avg_rating": "Avg Rating (★)",
                    "fulfillment_rate": "Fulfillment Rate (%)",
                    "refund_rate": "Refund Rate (%)"
                }
            ),
            use_container_width=True
        )
    else:
        leaderboard = pd.DataFrame()
        st.info("No active vendors found to compute leaderboard metrics.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 📊 PART 4: VENDOR ANALYTICS CHARTS
    # ==========================================
    st.markdown("### 📊 Vendor Analytics Visualizations")
    
    if not leaderboard.empty and "business_name" in leaderboard.columns and "total_revenue" in leaderboard.columns:
        chart_col1, chart_col2 = st.columns(2)
        top_n = min(10, len(leaderboard))
        bar_data = leaderboard.head(top_n).copy()

        with chart_col1:
            st.markdown("#### 💵 Top 10 Vendors by Revenue")
            fig_revenue_bar = px.bar(
                bar_data,
                x="total_revenue",
                y="business_name",
                orientation="h",
                labels={"total_revenue": "Revenue ($)", "business_name": "Vendor"},
                color="total_revenue",
                color_continuous_scale="Viridis"
            )
            fig_revenue_bar.update_layout(
                margin=dict(l=10, r=10, t=20, b=10), 
                height=340,
                showlegend=False,
                coloraxis_showscale=False,
                yaxis={"categoryorder": "total ascending"}
            )
            st.plotly_chart(fig_revenue_bar, use_container_width=True)
            
        with chart_col2:
            st.markdown("#### 📈 Rating vs Fulfillment Performance (Top 10)")
            bar_data["Rating (scaled to % value)"] = bar_data["avg_rating"] * 20 
            bar_data["Fulfillment (%)"] = bar_data["fulfillment_rate"]
            
            chart_data_scaled = bar_data.melt(
                id_vars=["business_name"],
                value_vars=["Rating (scaled to % value)", "Fulfillment (%)"],
                var_name="Indicator",
                value_name="Percentage Status"
            )

            fig_perf_bar = px.bar(
                chart_data_scaled,
                x="business_name",
                y="Percentage Status",
                color="Indicator",
                barmode="group",
                labels={"business_name": "Vendor Store", "Percentage Status": "Performance Index (%)"},
                color_discrete_sequence=["#F1C40F", "#2ECC71"]
            )
            fig_perf_bar.update_layout(
                margin=dict(l=10, r=10, t=20, b=80), 
                height=340,
                xaxis=dict(tickangle=-35),
                legend=dict(
                    orientation="h", 
                    y=1.2, 
                    x=0.5,
                    xanchor="center"
                ) 
            )
            st.plotly_chart(fig_perf_bar, use_container_width=True)
    else:
        st.info("Insufficient system dataset metrics available to populate visual tracking charts.")