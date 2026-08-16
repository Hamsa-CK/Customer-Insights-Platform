import os
import random
import pandas as pd
import streamlit as st

from modules.admin_portal import render_admin_dashboard
from modules.generator import generate_datasets
from modules.shared_reports import show_reports_engine
from modules.upload_dataset import render_upload_dataset_page
from modules.vendor_portal import render_vendor_dashboard

# Configure page layout
st.set_page_config(
    layout="wide", page_title="ShopSense Analytics Suite", page_icon="🛍️"
)

# Custom Enterprise-Grade Styling for Login & UI & Sidebar Redesign
st.markdown(
    """
    <style>
        /* Global & Background styling */
        .stApp {
            background: linear-gradient(135deg, #F5F2FF 0%, #FFFFFF 100%);
            color: #1E293B;
            font-family: 'Inter', 'Poppins', 'Manrope', sans-serif;
        }
        
        /* Remove top empty whitespace padding/margin block from Streamlit header */
        .stMainBlockContainer {
            padding-top: 1rem !important;
        }
        
        /* Hide default streamlit branding elements if needed */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}

        /* --- SIDEBAR UI/UX OVERHAUL (Enterprise SaaS Aesthetic) --- */
        section[data-testid="stSidebar"] {
            background-color: #FAFAFF !important;
            border-right: 1px solid #E8EAF5 !important;
            padding-top: 1rem !important;
            width: 270px !important;
            min-width: 270px !important;
            max-width: 270px !important;
            box-shadow: 4px 0 24px rgba(109, 74, 255, 0.03);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-left: 1.2rem !important;
            padding-right: 1.2rem !important;
        }

        /* Sidebar Logo Container */
        .sidebar-brand-container {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #FFFFFF;
            padding: 14px 16px;
            border-radius: 18px;
            border: 1px solid #E8EAF5;
            box-shadow: 0 4px 12px rgba(109, 74, 255, 0.04);
            margin-bottom: 16px;
        }

        /* Admin / User Information Card */
        .sidebar-user-card {
            background: #FFFFFF;
            padding: 12px 16px;
            border-radius: 18px;
            border: 1px solid #E8EAF5;
            box-shadow: 0 4px 12px rgba(109, 74, 255, 0.03);
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .sidebar-user-info {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 500;
            color: #64748B;
        }
        .admin-badge {
            background: linear-gradient(135deg, #6D4AFF 0%, #8B5CF6 100%);
            color: #FFFFFF;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 6px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            box-shadow: 0 2px 6px rgba(109, 74, 255, 0.2);
        }

        /* Main Menu Section Title */
        .sidebar-menu-title {
            font-size: 16px;
            font-weight: 700;
            color: #1E293B;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 12px;
            padding-left: 4px;
        }

        /* Custom Sidebar Clickable Navigation Buttons Styling (Inactive State) */
        section[data-testid="stSidebar"] div.stButton > button.nav-btn {
            background: #FFFFFF !important;
            color: #475569 !important;
            border-radius: 14px !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            border: 1px solid #E8EAF5 !important;
            box-shadow: 0 2px 8px rgba(109, 74, 255, 0.03) !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            padding: 10px 14px !important;
            text-align: left !important;
            display: flex !important;
            justify-content: flex-start !important;
            align-items: center !important;
            margin-bottom: 6px !important;
        }
        section[data-testid="stSidebar"] div.stButton > button.nav-btn:hover {
            background-color: #EFF6FF !important;
            border-color: #2563EB !important;
            color: #2563EB !important;
            transform: translateX(2px);
        }

        /* Custom Sidebar Logout Button (Always appear as solid blue style) */
        section[data-testid="stSidebar"] div.stButton > button.logout-btn {
            background: #2563EB !important;
            color: #FFFFFF !important;
            border-radius: 16px !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25) !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            padding: 12px 16px !important;
        }
        section[data-testid="stSidebar"] div.stButton > button.logout-btn:hover {
            background: #1D4ED8 !important;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.35) !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }

        /* Left Marketing Panel Cards */
        .feature-card {
            background: #FFFFFF;
            padding: 20px;
            border-radius: 20px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 10px 25px -5px rgba(109, 74, 255, 0.05);
            transition: all 0.3s ease;
            height: 100%;
        }
        .feature-card:hover {
            box-shadow: 0 20px 35px -10px rgba(109, 74, 255, 0.12);
            transform: translateY(-2px);
        }

        /* Bottom Feature Strip Container */
        .feature-strip {
            display: flex;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid #E5E7EB;
            padding: 16px 20px;
            border-radius: 16px;
            margin-top: 24px;
        }
        
        /* Right Login Panel Container styling overrides */
        .login-container {
            background: #FFFFFF;
            padding: 40px;
            border-radius: 24px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 20px 40px -15px rgba(109, 74, 255, 0.08);
        }

        /* Custom styling for standard Form Submit Buttons */
        div.stFormSubmitButton > button {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
            transition: all 0.3s ease !important;
        }
        div.stFormSubmitButton > button:hover {
            background-color: #1D4ED8 !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
            color: #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Ensure base datasets are initialized and are NOT empty (0 bytes)
parquet_path = "data/users.parquet"
if not os.path.exists(parquet_path) or os.path.getsize(parquet_path) == 0:
    generate_datasets()

# ⚡ OPTIMIZATION 1: Cache data loading in RAM so disk reads happen only once
@st.cache_data(ttl=600) 
def load_system_datasets():
    df_vendors = pd.read_parquet("data/vendors.parquet")
    df_products = pd.read_parquet("data/products.parquet")
    df_items = pd.read_parquet("data/order_items.parquet")
    df_orders = pd.read_parquet("data/orders.parquet")
    df_users = pd.read_parquet("data/users.parquet")
    df_reviews = (
        pd.read_parquet("data/reviews.parquet")
        if os.path.exists("data/reviews.parquet")
        else pd.DataFrame()
    )
    return df_vendors, df_products, df_items, df_orders, df_users, df_reviews

# Initialize dynamic routing state parameters
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.vendor_id = None

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "📊 Dashboard View"

# ==========================================
# 🚪 USER LOGIN & REGISTRATION INTERFACE
# ==========================================
if not st.session_state.logged_in:
    left_col, right_col = st.columns([1.3, 1], gap="large")

    with left_col:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
                <div style="background: #2563EB; padding: 10px; border-radius: 14px; display: inline-flex; box-shadow: 0 8px 20px rgba(37,99,235,0.3);">
                    <span style="font-size: 28px;">🛍️</span>
                </div>
                <h1 style='color: #1E293B; font-size: 32px; font-weight: 800; margin: 0;'>ShopSense</h1>
            </div>
            
            <h2 style='color: #1E293B; font-size: 38px; font-weight: 800; line-height: 1.2; margin-bottom: 16px;'>
                Next-Gen Unified <span style='color: #2563EB;'>Marketplace Suite</span>
            </h2>
            <p style='color: #64748B; font-size: 16px; line-height: 1.6; margin-bottom: 32px;'>
                Experience predictive demand forecasting, dynamic collaborative recommendation engines, real-time multi-vendor performance tracking, and advanced ML-driven customer churn risk modeling.
            </p>
            """,
            unsafe_allow_html=True,
        )

        card_col1, card_col2, card_col3 = st.columns(3, gap="medium")
        
        with card_col1:
            st.markdown(
                """
                <div class="feature-card">
                    <div style="background: #DCFCE7; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                        🛡️
                    </div>
                    <h4 style="color: #1E293B; font-size: 16px; font-weight: 700; margin-bottom: 8px;">For Administrators</h4>
                    <p style="color: #64748B; font-size: 13px; line-height: 1.4; margin-bottom: 16px;">Control seller approvals, rankings, and marketplace-wide CLV profiles.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
        with card_col2:
            st.markdown(
                """
                <div class="feature-card">
                    <div style="background: #EFF6FF; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                        🏬
                    </div>
                    <h4 style="color: #1E293B; font-size: 16px; font-weight: 700; margin-bottom: 8px;">For Vendors</h4>
                    <p style="color: #64748B; font-size: 13px; line-height: 1.4; margin-bottom: 16px;">Maintain store catalogs, predict stock requirements, and view buyer reviews.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with card_col3:
            st.markdown(
                """
                <div class="feature-card">
                    <div style="background: #FEF3C7; width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;">
                        💡
                    </div>
                    <h4 style="color: #1E293B; font-size: 16px; font-weight: 700; margin-bottom: 8px;">Demo Credentials</h4>
                    <p style="color: #64748B; font-size: 12px; line-height: 1.4; margin-bottom: 8px;">
                        <b>Admin:</b> admin@shopsense.com<br><b>Pass:</b> <code>admin</code><br>
                        <b>Vendor:</b> vendor1@shopsense.com<br><b>Pass:</b><code>password123</code><br>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="feature-strip">
                <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; font-weight: 600;">
                    📊 Real-Time Analytics
                </div>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; font-weight: 600;">
                    ⚡ Smart Forecasting
                </div>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; font-weight: 600;">
                    🤝 Vendor Collab
                </div>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; font-weight: 600;">
                    🔒 Secure & Scalable
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Removed tabs: auth_tab1, auth_tab2 = st.tabs(["🔒 Secure Login", "📝 Join as a Vendor"])
        # Displaying direct Secure Login UI
        st.markdown(
            """
            <div style="text-align: center; margin-top: 15px; margin-bottom: 20px;">
                <div style="background: #EFF6FF; width: 64px; height: 64px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 12px; box-shadow: 0 10px 20px rgba(37,99,235,0.15);">
                    <span style="font-size: 28px;">🔐</span>
                </div>
                <h3 style="color: #1E293B; font-weight: 800; font-size: 24px; margin: 0;">Welcome Back!</h3>
                <p style="color: #64748B; font-size: 14px; margin-top: 4px;">Log in to your ShopSense Dashboard.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            email_input = st.text_input(
                "Registered Email Address", value="admin@shopsense.com"
            )
            password_input = st.text_input(
                "Password", type="password", value="admin"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button(
                "Authenticate Portal Access", use_container_width=True
            )

            if submit_btn:
                (
                    df_vendors,
                    df_products,
                    df_items,
                    df_orders,
                    df_users,
                    df_reviews,
                ) = load_system_datasets()

                matched_user = df_users[
                    (df_users["email"] == email_input)
                    & (df_users["password"] == password_input)
                ]

                if not matched_user.empty:
                    user_record = matched_user.iloc[0]
                    user_role = user_record["role"]

                    if user_role == "vendor":
                        vendor_rec = df_vendors[
                            df_vendors["user_id"] == user_record["user_id"]
                        ]

                        if not vendor_rec.empty:
                            v_status = vendor_rec.iloc[0]["status"]
                            if v_status == "Pending":
                                st.error(
                                    "⏳ **Access Denied:** Your vendor account registration is pending review."
                                )
                                st.stop()
                            elif v_status == "Suspended":
                                st.error(
                                    "🚫 **Access Suspended:** This vendor account has been deactivated."
                                )
                                st.stop()

                        st.session_state.vendor_id = int(
                            vendor_rec.iloc[0]["vendor_id"]
                        )

                    st.session_state.logged_in = True
                    st.session_state.user_id = int(user_record["user_id"])
                    st.session_state.user_role = user_role
                    st.session_state.selected_page = "📊 Dashboard View"

                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Check email or password.")
        
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 12px; display: flex; align-items: center; gap: 12px; margin-top: 16px;">
                <span style="font-size: 18px;">🛡️</span>
                <span style="color: #64748B; font-size: 12px; line-height: 1.4;">Your data is encrypted and protected with enterprise-grade security.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

       

# ==========================================
# 🗺️ ACTIVE DASHBOARD ROUTING
# ==========================================
else:
    # --- REDESIGNED SIDEBAR MATCHING EXACT USER REQUIREMENTS ---
    with st.sidebar:
        # ShopSense Logo at the top
        st.markdown(
            """
            <div class="sidebar-brand-container">
                <div style="background: #2563EB; width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(37,99,235,0.2);">
                    <span style="font-size: 20px;">🛍️</span>
                </div>
                <span style="font-size: 18px; font-weight: 800; color: #1E293B;">ShopSense</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Admin/User Information Card
        role_upper = st.session_state.user_role.upper()
        badge_html = f'<span class="admin-badge">{role_upper}</span>' if role_upper == 'ADMIN' else f'<span style="background: #EFF6FF; color: #2563EB; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 6px; text-transform: uppercase;">{role_upper}</span>'
        
        st.markdown(
            f"""
            <div class="sidebar-user-card">
                <div class="sidebar-user-info">
                    <span>Logged in as</span>
                    {badge_html}
                </div>
                <div style="font-size: 12px; font-weight: 600; color: #1E293B; overflow: hidden; text-overflow: ellipsis;">
                    {st.session_state.user_role.capitalize()} Portal User
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # "MAIN MENU" section title
        st.markdown('<div class="sidebar-menu-title">MAIN MENU</div>', unsafe_allow_html=True)

        if st.session_state.user_role == "admin":
            menu_options = [
                "📊 Dashboard View",
                "📂 Upload Dataset",  # <-- ADD THIS SINGLE LINE
                "💰 Sales Analytics",
                "🛡️ Vendor Management",
                "📦 Product Management",
                "🧱 Inventory & Stocks",
                "👥 Customer Analytics",
                "🤖 ML Recommendations",
                "🔮 ML Forecasting",
                "⭐️ Reviews & Ratings",
                "📉 Churn Prediction",
                "📈 Report",
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
                "📈 Report",
            ]

        # Display navigation items safely with interactive styling
        for option in menu_options:
            is_active = (st.session_state.selected_page == option)
            safe_key_name = option.replace(" ", "_").replace("&", "_")
            
            if is_active:
                # Active option rendered reliably as a solid blue element
                st.markdown(
                    f"""
                    <div style="background: #2563EB; color: #FFFFFF; border-radius: 14px; font-weight: 700; font-size: 14px; padding: 10px 14px; margin-bottom: 6px; box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3); display: flex; align-items: center;">
                        {option}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                if st.button(option, key=f"nav_{safe_key_name}", use_container_width=True):
                    st.session_state.selected_page = option
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 5px 0 16px 0; border: none; border-top: 1px solid #E8EAF5;'>", unsafe_allow_html=True)

        # Close & session logout button
        if st.button("🚪 Close Session & Log Out", key="logout_btn", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()

    clean_selection = st.session_state.selected_page.split(" ", 1)[1]

    if st.session_state.user_role == "admin":
        if clean_selection == "Report":
            show_reports_engine(user_role="admin")
        elif clean_selection == "Upload Dataset":  # <-- ADD THIS ROUTE
            render_upload_dataset_page()
        else:
            render_admin_dashboard(active_tab=clean_selection)
    elif st.session_state.user_role == "vendor":
        if clean_selection == "Report":
            show_reports_engine(
                user_role="vendor", vendor_id=st.session_state.vendor_id
            )
        else:
            render_vendor_dashboard(
                active_tab=clean_selection, vendor_id=st.session_state.vendor_id
            )