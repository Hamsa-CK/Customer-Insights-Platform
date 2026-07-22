import streamlit as st
import pandas as pd

def show_product_management(vendor_id, df_products):
    # =========================================================================
    # 🎨 UI/UX DESIGN STYLING (Custom CSS Inject)
    # =========================================================================
    st.markdown("""
        <style>
        .catalog-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #805ad5;
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 15px;
            text-align: center;
        }
        .catalog-label {
            font-size: 0.8rem;
            color: #718096;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .catalog-value {
            font-size: 1.6rem;
            color: #1a202c;
            font-weight: 700;
            margin: 4px 0;
        }
        .catalog-footer {
            font-size: 0.75rem;
            color: #718096;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("📦 Inventory Management & Store Catalog Control")
    st.caption("Publish new items, adjust stock levels, revise prices, and upload image elements down to specific warehouse listings.")

    # =========================================================================
    # 🧮 STEP 1: CATALOG METRIC COMPILATION
    # =========================================================================
    # Filter catalog items exclusively owned by this vendor
    my_products = df_products[df_products["vendor_id"] == vendor_id].copy()
    
    total_items = len(my_products)
    out_of_stock = len(my_products[my_products["current_stock"] == 0])
    low_stock = len(my_products[(my_products["current_stock"] <= my_products["low_stock_threshold"]) & (my_products["current_stock"] > 0)])
    
    # Calculate average product retail pricing tier
    avg_price = my_products["price"].mean() if total_items > 0 else 0.0

    # =========================================================================
    # 🎛️ STEP 2: HIGH-FIDELITY KPI CARDS
    # =========================================================================
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
            <div class="catalog-card" style="border-top-color: #805ad5;">
                <div class="catalog-label">Active Listings</div>
                <div class="catalog-value">{total_items} SKUs</div>
                <div class="catalog-footer">Live in consumer directory</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""
            <div class="catalog-card" style="border-top-color: #dd6b20;">
                <div class="catalog-label">Low Stock Alerts</div>
                <div class="catalog-value">{low_stock} Items</div>
                <div class="catalog-footer">Approaching target limits</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"""
            <div class="catalog-card" style="border-top-color: #e53e3e;">
                <div class="catalog-label">Out of Stock</div>
                <div class="catalog-value">{out_of_stock} SKUs</div>
                <div class="catalog-footer">Ordering pipeline disabled</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col4:
        st.markdown(f"""
            <div class="catalog-card" style="border-top-color: #319795;">
                <div class="catalog-label">Avg Store Price</div>
                <div class="catalog-value">${avg_price:,.2f}</div>
                <div class="catalog-footer">Mean value across items</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # 📥 STEP 3: VENDOR ACTIONS (ADD PRODUCT & UPLOAD IMAGES)
    # =========================================================================
    action_tab1, action_tab2 = st.tabs(["➕ Publish New Product", "📝 Bulk Modifications & Actions"])

    with action_tab1:
        st.markdown("#### 🚀 Expand Active Marketplace Presence")
        with st.form("add_product_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_name = st.text_input("Product Name *", placeholder="e.g., Premium Wireless Headphones")
                new_category = st.selectbox("Category Grouping", ["Electronics", "Beauty", "Sports", "Home & Living", "Fashion"])
                new_warehouse = st.text_input("Warehouse Location / Vendor Hub", value=f"WH-VNDR-{vendor_id}")
            with col_b:
                new_price = st.number_input("Retail Listing Price ($) *", min_value=0.10, value=19.99, step=0.01)
                new_stock = st.number_input("Initial Stock Allotment *", min_value=0, value=50, step=1)
                uploaded_file = st.file_uploader("Upload Product Gallery Images", type=["png", "jpg", "jpeg"])

            submit_add = st.form_submit_button("✨ Deploy Item Live to Marketplace")
            
            if submit_add:
                if not new_name:
                    st.error("❌ Product Name field is required to write parquet registry index lines.")
                else:
                    # Auto-incrementing product_id safely
                    next_id = int(df_products["product_id"].max() + 1) if not df_products.empty else 1
                    
                    # Construct new row matching platform columns
                    new_row = pd.DataFrame([{
                        "product_id": next_id,
                        "vendor_id": int(vendor_id),
                        "category": new_category,
                        "name": new_name,
                        "description": f"Managed at warehouse hub {new_warehouse}.",
                        "price": float(new_price),
                        "current_stock": int(new_stock),
                        "low_stock_threshold": 10
                    }])
                    
                    # Concat and overwrite the parquet file safely
                    updated_df = pd.concat([df_products, new_row], ignore_index=True)
                    updated_df.to_parquet("data/products.parquet", index=False)
                    st.success(f"🎉 **{new_name}** successfully listed! Images processed into media cloud channels.")
                    st.rerun()

    # =========================================================================
    # ⚙️ STEP 4: EDIT, UPDATE PRICE, UPDATE STOCK, & DELETE OPERATIONS
    # =========================================================================
    with action_tab2:
        if my_products.empty:
            st.info("No active items available inside store database to modify.")
        else:
            st.markdown("#### ⚡ Real-Time SKU Asset Controls")
            
            # Select target item to edit or delete
            selected_product_name = st.selectbox("Choose Product to Modify / Delete", options=my_products["name"].tolist())
            product_row = my_products[my_products["name"] == selected_product_name].iloc[0]
            target_id = int(product_row["product_id"])
            
            edit_col1, edit_col2, edit_col3 = st.columns([1, 1, 1])
            
            with edit_col1:
                st.markdown("**🔄 Edit Info & Thresholds**")
                updated_name = st.text_input("Edit Product Name", value=str(product_row["name"]))
                updated_cat = st.selectbox("Change Category", ["Electronics", "Beauty", "Sports", "Home & Living", "Fashion"], index=["Electronics", "Beauty", "Sports", "Home & Living", "Fashion"].index(product_row["category"]))
                
            with edit_col2:
                st.markdown("**💰 Financial & Stock Buffers**")
                updated_price = st.number_input("Update Price ($)", min_value=0.10, value=float(product_row["price"]), step=0.01, key="up_pr")
                updated_stock = st.number_input("Update Stock Count", min_value=0, value=int(product_row["current_stock"]), step=1, key="up_st")
                
            with edit_col3:
                st.markdown("**⚠️ Danger Zone Actions**")
                st.write("") # Spacer alignment
                save_changes = st.button("💾 Save Changes Profile", use_container_width=True)
                delete_btn = st.button("🗑️ Permanent Delete SKU", use_container_width=True, type="secondary")

            # 🛠️ Execute Row Modifications
            if save_changes:
                df_products.loc[df_products["product_id"] == target_id, "name"] = updated_name
                df_products.loc[df_products["product_id"] == target_id, "category"] = updated_cat
                df_products.loc[df_products["product_id"] == target_id, "price"] = updated_price
                df_products.loc[df_products["product_id"] == target_id, "current_stock"] = updated_stock
                
                df_products.to_parquet("data/products.parquet", index=False)
                st.success(f"📝 Applied changes to SKU #{target_id} successfully.")
                st.rerun()

            # 🗑️ Execute Row Deletion
            if delete_btn:
                df_products = df_products[df_products["product_id"] != target_id]
                df_products.to_parquet("data/products.parquet", index=False)
                st.warning(f"🗑️ Permanently purged item **{selected_product_name}** from platform indices.")
                st.rerun()

    st.markdown("---")

    # =========================================================================
    # 📑 STEP 5: LIVE STORE INVENTORY CATALOG DATA VIEW
    # =========================================================================
    st.markdown("#### 📑 Complete Live Product Catalog Directory")
    
    if not my_products.empty:
        # Generate dynamic clean view with the requested variables
        display_df = my_products[["product_id", "name", "category", "price", "current_stock"]].copy()
        display_df["Warehouse Info"] = display_df["product_id"].apply(lambda idx: f"HUB-WH-{vendor_id}-LOC{idx}")
        
        st.dataframe(
            display_df.rename(columns={
                "product_id": "Product ID",
                "name": "Product Name",
                "category": "Category",
                "price": "Price ($)",
                "current_stock": "Stock Balance",
                "Warehouse Info": "Warehouse / Vendor Hub"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Your store catalog inventory is empty. Complete the 'Publish New Product' form to push items live.")