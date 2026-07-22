import streamlit as st
import pandas as pd

# Import modular admin sub-pages
from modules.admin.dashboard import show_dashboard
from modules.admin.sales_analytics import show_sales_analytics
from modules.admin.vendor_management import show_vendor_management
from modules.admin.product_management import show_product_management
from modules.admin.inventory_stocks import show_inventory_stocks
from modules.admin.customer_analytics import show_customer_analytics
from modules.admin.ml_recommendation import show_recommendation_system
from modules.admin.ml_forecasting import show_ml_forecasting
from modules.admin.churn_prediction import show_churn_clv_analysis
from modules.shared_reports import show_reports_engine

def render_admin_dashboard(active_tab):
    # Load primary data sources safely
    df_vendors = pd.read_parquet("data/vendors.parquet")
    df_products = pd.read_parquet("data/products.parquet")
    df_orders = pd.read_parquet("data/orders.parquet")
    df_customers = pd.read_parquet("data/customers.parquet")
    df_items = pd.read_parquet("data/order_items.parquet")

    # Routing core with flexible string matching
    if active_tab == "Dashboard View":
        show_dashboard(df_products, df_orders, df_vendors, df_customers, df_items)
        
    elif active_tab == "Sales Analytics":
        show_sales_analytics(df_orders, df_items, df_products)
        
    elif active_tab == "Vendor Management":
        show_vendor_management(df_vendors, df_items, df_orders, df_reviews=None)
        
    elif active_tab == "Product Management":
        show_product_management(df_products, df_vendors, df_items)
        
    elif active_tab == "Inventory & Stocks":
        show_inventory_stocks(df_products, df_items, df_orders)
        
    elif active_tab == "Customer Analytics":
        show_customer_analytics(df_customers, df_orders)
        
    elif active_tab in ["Recommendation System", "ML Recommendations"]:
        show_recommendation_system(df_products, df_items, df_orders, df_customers)
        
    elif active_tab in ["ML Forecasting", "ML forecasting"]:
        show_ml_forecasting(df_orders, df_items, df_products, df_customers, df_vendors)
        
    # --- FIXED LINE: Added "Churn Prediction" to explicitly catch the sidebar click event ---
    elif active_tab in ["Churn & CLV", "Churn prediction and clv", "Churn Prediction"]:
        show_churn_clv_analysis(df_customers, df_orders, df_items, df_products)

    elif active_tab == "Report":
        # 👑 Trigger the shared executive reporting suite with admin credentials
        show_reports_engine(user_role="admin")

    
        
    else:
        st.subheader(f"🛡️ Admin Command Center - {active_tab}")
        st.caption("Custom operations view")
        st.markdown("---")
        st.warning(f"🚧 The **{active_tab}** module is ready for configuration next!")