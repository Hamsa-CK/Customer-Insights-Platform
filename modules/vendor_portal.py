import streamlit as st
import pandas as pd
import os

# =========================================================================
# 📦 STEP 1: EXPLICIT MODULAR IMPORT PIPELINE
# =========================================================================
from modules.vendor.dashboard import show_vendor_dashboard
from modules.vendor.sales_analytics import show_sales_analytics
from modules.vendor.product_management import show_product_management
from modules.vendor.inventory_stocks import show_inventory_stocks
from modules.vendor.customer_analytics import show_customer_analytics
from modules.vendor.ml_forecasting import show_ml_forecasting
from modules.vendor.ml_recommendation import show_ml_recommendation
from modules.shared_reports import show_reports_engine


def render_vendor_dashboard(active_tab, current_user_id=None, vendor_id=None):
    """
    Core Entry Router for the Vendor Dashboard Workspace.
    Loads relational Parquet states, normalizes types to bypass the $0.00 data mismatch bug,
    and forwards explicitly filtered sets down to individual functional components.
    """
    # 1. Structural Layer Guard Verification
    required_files = ["vendors.parquet", "products.parquet", "orders.parquet", "order_items.parquet"]
    for file in required_files:
        if not os.path.exists(f"data/{file}"):
            st.error(f"❌ Critical Error: Base infrastructure file `data/{file}` is missing from disk.")
            return

    # 2. Extract Base Datasets Cleanly
    df_vendors = pd.read_parquet("data/vendors.parquet")
    df_products = pd.read_parquet("data/products.parquet")
    df_orders = pd.read_parquet("data/orders.parquet")
    df_items = pd.read_parquet("data/order_items.parquet")
    
    try:
        df_reviews = pd.read_parquet("data/reviews.parquet")
    except Exception:
        df_reviews = pd.DataFrame()

    try:
        df_customers = pd.read_parquet("data/customers.parquet")
    except Exception:
        df_customers = pd.DataFrame()

    # =========================================================================
    # 🛠️ FIXED: STEP 3: RESOLVE STRUCTURAL LINKED VENDOR PROFILE
    # =========================================================================
    # Check vendor_id first if explicitly passed, bypassing column cross-contamination
    if vendor_id is not None:
        vendor_row = df_vendors[df_vendors["vendor_id"] == int(vendor_id)]
    else:
        vendor_row = df_vendors[df_vendors["user_id"] == current_user_id]
        
    if vendor_row.empty:
        st.error("❌ Authentication Linkage Error: Could not verify a matching Vendor Profile.")
        return
        
    # Extract structural profile variables 
    vendor_id = int(vendor_row.iloc[0]["vendor_id"])
    business_name = vendor_row.iloc[0]["business_name"]
    owner_name = vendor_row.iloc[0]["owner_name"]
    city = vendor_row.iloc[0].get("city", "Unknown")
    commission = float(vendor_row.iloc[0].get("commission_percentage", 10.0))

    # 4. Global Normalized Data-Type Typecasting (Fixes the $0.00 silent matching bug)
    df_items["vendor_id"] = df_items["vendor_id"].astype(int)
    df_products["vendor_id"] = df_products["vendor_id"].astype(int)

    # 5. Core Global Header Sticky UI
    st.title(f"🏬 {business_name}")
    st.caption(f"Manager: {owner_name} | Location: {city} | Platform Fee: {commission}%")
    st.markdown("---")

    # =========================================================================
    # 🎛️ STEP 2: MODULAR SIDEBAR ROUTING ENGINE MATRIX
    # =========================================================================
    if active_tab == "Dashboard View":
        show_vendor_dashboard(vendor_id, df_products, df_items, df_orders)
        
    elif active_tab == "Sales Analytics":
        show_sales_analytics(vendor_id, df_items, df_orders, df_products)
        
    elif active_tab == "Product Management":
        show_product_management(vendor_id, df_products)
        
    elif active_tab == "Inventory & Stocks":
        show_inventory_stocks(vendor_id, df_products, df_items)
        
    elif active_tab == "Customer Analytics":
        show_customer_analytics(vendor_id, df_items, df_orders, df_customers)
        
    elif active_tab == "ML Forecasting":
        show_ml_forecasting(vendor_id, df_items, df_orders, df_products)
        
    elif active_tab == "ML Recommendations":
        # Includes df_orders to avoid missing argument exceptions
        show_ml_recommendation(vendor_id, df_items, df_orders, df_products)

    elif active_tab == "Report":
        # ✅ Trigger the reporting shared module for the active vendor account instance
        show_reports_engine(user_role="vendor", vendor_id=vendor_id)
        
    else:
        st.error(f"🚨 Navigation Path Error: Sub-module target '{active_tab}' not established inside router matrix.")