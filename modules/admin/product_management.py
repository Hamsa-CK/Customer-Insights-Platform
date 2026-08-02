import streamlit as st
import pandas as pd
import plotly.express as px
import os

def show_product_management(df_products, df_vendors, df_items):
    
    st.markdown(
        """
        <div style="background-color: #9370DB; padding: 20px 30px; border-radius: 0px; margin-left: -5rem; margin-right: -5rem; margin-top: -2rem; margin-bottom: 25px;">
            <h3 style="color: white; margin: 0; font-size: 32px;">📦 Global Marketplace Catalog</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clean & Deep Copy DataFrames
    df_products = df_products.copy() if df_products is not None else pd.DataFrame()
    df_vendors = df_vendors.copy() if df_vendors is not None else pd.DataFrame()
    df_items = df_items.copy() if df_items is not None else pd.DataFrame()

    # Ensure status column exists in products
    if "status" not in df_products.columns:
        df_products["status"] = "Active"

    # ==========================================
    # 🔍 PART 1: SEARCH & FILTER CONTROL BAR
    # ==========================================
    st.markdown("### 🔍 Search & Filters")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        search_query = st.text_input("Search Products by Name", "").strip().lower()
        
    with f_col2:
        if not df_vendors.empty and "business_name" in df_vendors.columns:
            vendor_options = ["All Vendors"] + df_vendors["business_name"].dropna().unique().tolist()
        else:
            vendor_options = ["All Vendors"]
        selected_vendor = st.selectbox("Filter by Vendor", vendor_options)
        
    with f_col3:
        if not df_products.empty and "category" in df_products.columns:
            category_options = ["All Categories"] + df_products["category"].dropna().unique().tolist()
        else:
            category_options = ["All Categories"]
        selected_category = st.selectbox("Filter by Category", category_options)

    # Apply Search & Filter logic dynamically
    filtered_products = df_products.copy()
    
    if search_query and "name" in filtered_products.columns:
        filtered_products = filtered_products[filtered_products["name"].astype(str).str.lower().str.contains(search_query)]
        
    if selected_vendor != "All Vendors" and not df_vendors.empty and "business_name" in df_vendors.columns:
        vendor_match = df_vendors[df_vendors["business_name"] == selected_vendor]
        if not vendor_match.empty and "vendor_id" in vendor_match.columns:
            vendor_id = vendor_match.iloc[0]["vendor_id"]
            if "vendor_id" in filtered_products.columns:
                filtered_products = filtered_products[filtered_products["vendor_id"] == vendor_id]
        
    if selected_category != "All Categories" and "category" in filtered_products.columns:
        filtered_products = filtered_products[filtered_products["category"] == selected_category]

    # Merge vendor names for clearer grid rendering
    if not filtered_products.empty and "vendor_id" in filtered_products.columns and not df_vendors.empty and "vendor_id" in df_vendors.columns and "business_name" in df_vendors.columns:
        merged_display = pd.merge(filtered_products, df_vendors[["vendor_id", "business_name"]], on="vendor_id", how="left")
    else:
        merged_display = filtered_products.copy()
        if "business_name" not in merged_display.columns:
            merged_display["business_name"] = "N/A"

    # Ensure all expected columns exist in merged_display
    for col in ["product_id", "name", "category", "business_name", "price", "current_stock", "status"]:
        if col not in merged_display.columns:
            merged_display[col] = "N/A"

    # ==========================================
    # 📋 PART 2: VIEW PRODUCTS GRID & MANAGING OPERATIONS
    # ==========================================
    
    st.markdown(
        f"""
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">🗃️ Listed Items ({len(merged_display)} total matches)</h3>
        """,
        unsafe_allow_html=True,
    )

    
    
    # Display product catalog grid
    st.dataframe(
        merged_display[["product_id", "name", "category", "business_name", "price", "current_stock", "status"]].rename(
            columns={
                "product_id": "Product ID",
                "name": "Product Name",
                "category": "Category",
                "business_name": "Vendor Name",
                "price": "Price ($)",
                "current_stock": "In Stock",
                "status": "Status"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### ⚡ Manage Product Listing Flags & Statuses")
    
    if not merged_display.empty and "name" in merged_display.columns:
        op_col1, op_col2, op_col3 = st.columns([2, 1, 1])
        
        with op_col1:
            prod_names = [n for n in merged_display["name"].tolist() if n != "N/A"]
            if prod_names:
                selected_prod_name = st.selectbox(
                    "Choose Product to Edit", 
                    options=prod_names,
                    key="prod_status_select"
                )
                prod_matches = df_products[df_products["name"] == selected_prod_name]
                if not prod_matches.empty:
                    prod_row = prod_matches.iloc[0]
                    prod_id = prod_row["product_id"]
                    current_status = prod_row.get("status", "Active")
                else:
                    prod_id = None
                    current_status = "Active"
            else:
                selected_prod_name = None
                prod_id = None
                current_status = "Active"
            
        if prod_id is not None:
            with op_col2:
                # Enable / Disable Switcher
                if current_status == "Active":
                    if st.button("🚫 Disable Product", use_container_width=True, key=f"dis_{prod_id}"):
                        df_products.loc[df_products["product_id"] == prod_id, "status"] = "Disabled"
                        os.makedirs("data", exist_ok=True)
                        try:
                            df_products.to_parquet("data/products.parquet", index=False)
                        except Exception as e:
                            st.error(f"Could not save changes: {e}")
                        st.warning(f"Disabled {selected_prod_name} listings.")
                        st.rerun()
                else:
                    if st.button("🟢 Enable Product", use_container_width=True, key=f"en_{prod_id}"):
                        df_products.loc[df_products["product_id"] == prod_id, "status"] = "Active"
                        os.makedirs("data", exist_ok=True)
                        try:
                            df_products.to_parquet("data/products.parquet", index=False)
                        except Exception as e:
                            st.error(f"Could not save changes: {e}")
                        st.success(f"Enabled {selected_prod_name} listing on marketplace.")
                        st.rerun()
                        
            with op_col3:
                # Physical deletion button
                if st.button("🗑️ Delete Product", use_container_width=True, key=f"del_{prod_id}"):
                    updated_products = df_products[df_products["product_id"] != prod_id]
                    os.makedirs("data", exist_ok=True)
                    try:
                        updated_products.to_parquet("data/products.parquet", index=False)
                    except Exception as e:
                        st.error(f"Could not save changes: {e}")
                    st.error(f"Permanently removed {selected_prod_name} from the database.")
                    st.rerun()
    else:
        st.info("No matching listings found.")

    st.markdown("---")

    # ==========================================
    # 📈 PART 3: PRODUCT ANALYTICS
    # ==========================================
    
    st.markdown(
        """
        <div style="border: 2px solid #E5E7EB; padding:10px 15px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: #1F2937;">📊 Catalog Analytics</h3>
        """,
        unsafe_allow_html=True,
    )

    
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.markdown("#### 🏷️ Product Catalog Share by Category")
        if not df_products.empty and "category" in df_products.columns:
            category_counts = df_products["category"].value_counts().reset_index()
            category_counts.columns = ["Category", "Product Count"]
            
            fig_pie = px.pie(
                category_counts,
                names="Category",
                values="Product Count",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No category data available.")
        
    with c_col2:
        st.markdown("#### ⚡ Top 10 High Volume Demand Items")
        if not df_items.empty and "product_id" in df_items.columns and "quantity" in df_items.columns and not df_products.empty and "product_id" in df_products.columns:
            top_sales = df_items.groupby("product_id")["quantity"].sum().reset_index()
            top_sales_merged = pd.merge(top_sales, df_products, on="product_id", how="inner").sort_values(by="quantity", ascending=False).head(10)
            
            if not top_sales_merged.empty and "name" in top_sales_merged.columns:
                fig_bar = px.bar(
                    top_sales_merged,
                    x="quantity",
                    y="name",
                    orientation="h",
                    labels={"quantity": "Units Sold", "name": "Product"},
                    color="quantity",
                    color_continuous_scale="Cividis"
                )
                fig_bar.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, coloraxis_showscale=False, yaxis={"categoryorder":"total ascending"})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No item sales data found.")
        else:
            st.info("Insufficient item transaction records.")