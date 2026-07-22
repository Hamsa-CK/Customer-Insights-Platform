import streamlit as st
import pandas as pd
import os
import random
from modules.generator import generate_datasets
from modules.admin_portal import render_admin_dashboard
from modules.vendor_portal import render_vendor_dashboard
from modules.shared_reports import show_reports_engine

# Configure page layout
st.set_page_config(layout="wide", page_title="ShopSense Analytics Suite", page_icon="🛍️")

# Ensure base datasets are initialized and are NOT empty (0 bytes)
parquet_path = "data/users.parquet"
if not os.path.exists(parquet_path) or os.path.getsize(parquet_path) == 0:
    generate_datasets()

# Initialize dynamic routing state parameters
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.vendor_id = None

# 🔄 1. Function to force reload fresh files into memory
def reload_system_datasets():
    st.session_state.df_vendors = pd.read_parquet("data/vendors.parquet")
    st.session_state.df_products = pd.read_parquet("data/products.parquet")
    st.session_state.df_items = pd.read_parquet("data/order_items.parquet")
    st.session_state.df_orders = pd.read_parquet("data/orders.parquet")
    if os.path.exists("data/reviews.parquet"):
        st.session_state.df_reviews = pd.read_parquet("data/reviews.parquet")

# ==========================================
# 🚪 USER LOGIN & REGISTRATION INTERFACE
# ==========================================
if not st.session_state.logged_in:
    # 2-Column Split-Screen Layout for a modern visual balance
    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <h1 style='color: #1F618D; font-size: 42px; margin-bottom: 5px;'>🛍️ ShopSense</h1>
            <h3 style='color: #5D6D7E; font-weight: 400; margin-top: 0;'>Next-Gen Unified Marketplace Suite</h3>
            <p style='color: #7F8C8D; font-size: 16px; line-height: 1.6;'>
                Welcome to the analytics and inventory operations hub. Experience predictive demand forecasting, 
                dynamic collaborative recommendation engines, real-time multi-vendor performance tracking, 
                and advanced ML-driven customer churn risk modeling.
            </p>
            """, 
            unsafe_allow_html=True
        )
        
        # Displaying platform highlights as modern styled cards
        st.markdown(
            """
            <div style="background-color: #F8F9F9; padding: 15px; border-radius: 8px; border-left: 5px solid #2980B9; margin-bottom: 12px;">
                <h5 style="margin: 0; color: #2C3E50;">🛡️ For Administrators</h5>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #7F8C8D;">Control seller approvals, manage vendor rankings, and view marketplace-wide CLV profiles.</p>
            </div>
            <div style="background-color: #F8F9F9; padding: 15px; border-radius: 8px; border-left: 5px solid #8E44AD; margin-bottom: 12px;">
                <h5 style="margin: 0; color: #2C3E50;">🏬 For Vendors</h5>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #7F8C8D;">Maintain your isolated store catalog, predict product stock requirements, and view private buyer reviews.</p>
            </div>
            <div style="background-color: #FAFAFA; padding: 15px; border-radius: 8px; border-left: 5px solid #27AE60;">
                <h5 style="margin: 0; color: #2C3E50;">💡 Demo Login Credentials</h5>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #7F8C8D;">
                    <b>Admin:</b> admin@shopsense.com / password: <code>admin</code><br>
                    <b>Vendor 1:</b> vendor1@shopsense.com / password: <code>password123</code>
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    with right_col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Toggle tabs for logging in vs registering as a new vendor
        auth_tab1, auth_tab2 = st.tabs(["🔒 Secure Login", "📝 Join as a Vendor"])

        # ------------------- TAB 1: LOGIN FORM -------------------
        with auth_tab1:
            with st.form("login_form"):
                st.markdown("### Log in to your Dashboard")
                email_input = st.text_input("Registered Email Address", value="admin@shopsense.com")
                password_input = st.text_input("Password", type="password", value="admin")
                
                # Full-width blue colored submit button
                submit_btn = st.form_submit_button("Authenticate Portal Access", use_container_width=True)
                
                if submit_btn:
                    df_users = pd.read_parquet("data/users.parquet")
                    matched_user = df_users[(df_users["email"] == email_input) & (df_users["password"] == password_input)]
                    
                    if not matched_user.empty:
                        user_record = matched_user.iloc[0]
                        user_role = user_record["role"]
                        
                        # Handle Vendor-specific status parameters before authorizing login
                        if user_role == "vendor":
                            df_vendors = pd.read_parquet("data/vendors.parquet")
                            vendor_rec = df_vendors[df_vendors["user_id"] == user_record["user_id"]]
                            
                            if not vendor_rec.empty:
                                v_status = vendor_rec.iloc[0]["status"]
                                if v_status == "Pending":
                                    st.error("⏳ **Access Denied:** Your vendor account registration is pending review by our administrator team.")
                                    st.stop()
                                elif v_status == "Suspended":
                                    st.error("🚫 **Access Suspended:** This vendor account has been deactivated. Please contact support.")
                                    st.stop()
                                
                                st.session_state.vendor_id = int(vendor_rec.iloc[0]["vendor_id"])
                        
                        # Set active session variables
                        st.session_state.logged_in = True
                        st.session_state.user_id = int(user_record["user_id"])
                        st.session_state.user_role = user_role
                        
                        # 🔄 2. FORCE DATASET RE-LOADING ON SUCCESSFUL AUTHENTICATION
                        reload_system_datasets()
                        
                        st.success("Authentication successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials. Please check your email or password.")

        # ------------------- TAB 2: VENDOR REGISTRATION -------------------
        with auth_tab2:
            with st.form("vendor_reg_form"):
                st.markdown("### Register your Business")
                reg_email = st.text_input("Business Email Address")
                reg_pass = st.text_input("Choose Password", type="password")
                reg_shop = st.text_input("Store/Business Name")
                reg_owner = st.text_input("Owner's Full Name")
                
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    reg_gst = st.text_input("GST/Tax Number", max_chars=15, help="Format: 15-character alphanumeric code")
                with col_sub2:
                    reg_phone = st.text_input("Contact Phone")
                
                col_sub3, col_sub4 = st.columns(2)
                with col_sub3:
                    reg_city = st.text_input("City")
                with col_sub4:
                    reg_state = st.text_input("State")

                register_btn = st.form_submit_button("Submit Application", use_container_width=True)

                if register_btn:
                    if not (reg_email and reg_pass and reg_shop and reg_owner and reg_gst):
                        st.warning("⚠️ Please fill out all required fields marked with an asterisk.")
                    else:
                        # Load databases to append new user
                        df_users = pd.read_parquet("data/users.parquet")
                        df_vendors = pd.read_parquet("data/vendors.parquet")

                        # Validate unique email constraint
                        if reg_email in df_users["email"].values:
                            st.error("❌ An account with this email address already exists.")
                        else:
                            # 1. Create User Base Login entry
                            new_user_id = int(df_users["user_id"].max() + 1)
                            new_user_df = pd.DataFrame([{
                                "user_id": new_user_id,
                                "email": reg_email,
                                "password": reg_pass,
                                "role": "vendor"
                            }])
                            df_users = pd.concat([df_users, new_user_df], ignore_index=True)
                            df_users.to_parquet("data/users.parquet", index=False)

                            # 2. Create Vendor Profile entry (Defaulting Status to "Pending")
                            new_vendor_id = int(df_vendors["vendor_id"].max() + 1)
                            new_vendor_df = pd.DataFrame([{
                                "vendor_id": new_vendor_id,
                                "user_id": new_user_id,
                                "business_name": reg_shop,
                                "owner_name": reg_owner,
                                "phone": reg_phone,
                                "gst_number": reg_gst.upper(),
                                "address": f"Suite {random.randint(100,999)}",
                                "city": reg_city,
                                "state": reg_state,
                                "commission_percentage": 10.0,
                                "status": "Pending"
                            }])
                            df_vendors = pd.concat([df_vendors, new_vendor_df], ignore_index=True)
                            df_vendors.to_parquet("data/vendors.parquet", index=False)

                            st.success("🎉 Registration Successful! Your profile is now in the Admin's queue for review.")
                            st.info("💡 Try logging in with 'admin@shopsense.com' to review and approve your newly registered shop!")

# ==========================================
# 🗺️ ACTIVE DASHBOARD ROUTING (SIDEBAR NAVIGATION)
# ==========================================
else:
    # Sidebar Header Info
    st.sidebar.markdown(f"### 🛍️ ShopSense Suite")
    st.sidebar.markdown(f"👤 **Logged in as:** `{st.session_state.user_role.upper()}`")
    st.sidebar.markdown("---")

    # Dynamic Sidebar Navigation Configuration
    if st.session_state.user_role == "admin":
        menu_options = [
            "📊 Dashboard View",
            "💰 Sales Analytics",
            "🛡️ Vendor Management",
            "📦 Product Management",
            "🧱 Inventory & Stocks",
            "👥 Customer Analytics",
            "🤖 ML Recommendations",
            "🔮 ML Forecasting",
            "📉 Churn Prediction",
            "📈 Report"  # Explicitly added to the Admin options
        ]
    else:
        menu_options = [
            "📊 Dashboard View",
            "💰 Sales Analytics",
            "📦 Product Management",
            "🧱 Inventory & Stocks",
            "👥 Customer Analytics",
            "🔮 ML Forecasting",
            "🎯 ML Recommendations",
            "⭐️ Reviews & Ratings",
            "📝 Order Management",
            "💳 Payment Management",
            "📈 Report"  # Explicitly added to the Vendor options
        ]

    # Render Navigation Select Box instead of Radio Buttons
    selected_page = st.sidebar.selectbox("🧭 Navigation Menu", menu_options)
    
    st.sidebar.markdown("---")
    
    # Session Exit Option
    if st.sidebar.button("🔌 Close Session & Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # Route content depending on selection
    # Clean string to remove emojis for router logic
    clean_selection = selected_page.split(" ", 1)[1]

    if st.session_state.user_role == "admin":
        if clean_selection == "Report":
            show_reports_engine(user_role="admin")
        else:
            render_admin_dashboard(active_tab=clean_selection)
    elif st.session_state.user_role == "vendor":
        if clean_selection == "Report":
            show_reports_engine(user_role="vendor", vendor_id=st.session_state.vendor_id)
        else:
            render_vendor_dashboard(active_tab=clean_selection, vendor_id=st.session_state.vendor_id)