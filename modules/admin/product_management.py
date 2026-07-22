import streamlit as st
import pandas as pd
import plotly.express as px

def show_product_management(df_products, df_vendors, df_items):
    st.subheader("📦 Global Marketplace Catalog")

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
        vendor_options = ["All Vendors"] + df_vendors["business_name"].unique().tolist()
        selected_vendor = st.selectbox("Filter by Vendor", vendor_options)
        
    with f_col3:
        category_options = ["All Categories"] + df_products["category"].unique().tolist()
        selected_category = st.selectbox("Filter by Category", category_options)

    # Apply Search & Filter logic dynamically
    filtered_products = df_products.copy()
    
    if search_query:
        filtered_products = filtered_products[filtered_products["name"].str.lower().str.contains(search_query)]
        
    if selected_vendor != "All Vendors":
        vendor_id = df_vendors[df_vendors["business_name"] == selected_vendor].iloc[0]["vendor_id"]
        filtered_products = filtered_products[filtered_products["vendor_id"] == vendor_id]
        
    if selected_category != "All Categories":
        filtered_products = filtered_products[filtered_products["category"] == selected_category]

    # Merge vendor names for clearer grid rendering
    merged_display = pd.merge(filtered_products, df_vendors[["vendor_id", "business_name"]], on="vendor_id", how="left")

    # ==========================================
    # 📋 PART 2: VIEW PRODUCTS GRID & MANAGING OPERATIONS
    # ==========================================
    st.markdown(f"### 🗃️ Listed Items ({len(merged_display)} total matches)")
    
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
    
    if not merged_display.empty:
        op_col1, op_col2, op_col3 = st.columns([2, 1, 1])
        
        with op_col1:
            selected_prod_name = st.selectbox(
                "Choose Product to Edit", 
                options=merged_display["name"].tolist(),
                key="prod_status_select"
            )
            prod_row = df_products[df_products["name"] == selected_prod_name].iloc[0]
            prod_id = prod_row["product_id"]
            current_status = prod_row.get("status", "Active")
            
        with op_col2:
            # Enable / Disable Switcher
            if current_status == "Active":
                if st.button("🚫 Disable Product", use_container_width=True, key=f"dis_{prod_id}"):
                    df_products.loc[df_products["product_id"] == prod_id, "status"] = "Disabled"
                    df_products.to_parquet("data/products.parquet", index=False)
                    st.warning(f"Disabled {selected_prod_name} listings.")
                    st.rerun()
            else:
                if st.button("🟢 Enable Product", use_container_width=True, key=f"en_{prod_id}"):
                    df_products.loc[df_products["product_id"] == prod_id, "status"] = "Active"
                    df_products.to_parquet("data/products.parquet", index=False)
                    st.success(f"Enabled {selected_prod_name} listing on marketplace.")
                    st.rerun()
                    
        with op_col3:
            # Physical deletion button
            if st.button("🗑️ Delete Product", use_container_width=True, key=f"del_{prod_id}"):
                # Filter out the deleted row entirely
                updated_products = df_products[df_products["product_id"] != prod_id]
                updated_products.to_parquet("data/products.parquet", index=False)
                st.error(f"Permanently removed {selected_prod_name} from the database.")
                st.rerun()
    else:
        st.info("No matching listings found.")

    st.markdown("---")

    # ==========================================
    # 📈 PART 3: PRODUCT ANALYTICS
    # ==========================================
    st.markdown("### 📊 Catalog Analytics")
    
    c_col1, c_col2 = st.columns(2)
    
    with c_col1:
        st.markdown("#### 🏷️ Product Catalog Share by Category")
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
        
    with c_col2:
        st.markdown("#### ⚡ Top 10 High Volume Demand Items")
        # Aggregating unit sales across orders items database
        top_sales = df_items.groupby("product_id")["quantity"].sum().reset_index()
        top_sales_merged = pd.merge(top_sales, df_products, on="product_id").sort_values(by="quantity", ascending=False).head(10)
        
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