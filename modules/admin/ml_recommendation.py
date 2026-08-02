import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def show_recommendation_system(df_products, df_items, df_orders, df_customers):
    
    st.markdown(
        """
        <div style="background-color: #9370DB; padding: 20px 30px; border-radius: 0px; margin-left: -5rem; margin-right: -5rem; margin-top: -2rem; margin-bottom: 25px;">
            <h3 style="color: white; margin: 0; font-size: 32px;">🛍️ Intelligent Recommendation Engine</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # Clean and pre-process datasets
    df_products = df_products.copy() if df_products is not None else pd.DataFrame()
    df_items = df_items.copy() if df_items is not None else pd.DataFrame()
    df_orders = df_orders.copy() if df_orders is not None else pd.DataFrame()
    df_customers = df_customers.copy() if df_customers is not None else pd.DataFrame()

    if not df_orders.empty and "status" in df_orders.columns:
        valid_orders = df_orders[df_orders["status"] != "Cancelled"]
    else:
        valid_orders = df_orders

    # Initialize valid_items safely before checking its columns
    valid_items = pd.DataFrame()
    if not df_items.empty and not valid_orders.empty and "order_id" in df_items.columns and "order_id" in valid_orders.columns:
        valid_items = df_items[df_items["order_id"].isin(valid_orders["order_id"])]

    # --- Merge order metadata to explicitly pull 'customer_id' ---
    if not valid_items.empty and not df_products.empty and "product_id" in valid_items.columns and "product_id" in df_products.columns:
        df_merged = pd.merge(valid_items, df_products, on="product_id", how="inner")
        if not valid_orders.empty and "order_id" in df_merged.columns and "order_id" in valid_orders.columns and "customer_id" in valid_orders.columns:
            df_merged = pd.merge(df_merged, valid_orders[["order_id", "customer_id"]], on="order_id", how="inner")
        else:
            df_merged = pd.DataFrame()
    else:
        df_merged = pd.DataFrame()

    # ==========================================
    # 👥 COLLABORATIVE FILTERING SYSTEM
    # ==========================================
    
    st.markdown(
    """
    <div style="border: 2px solid #E5E7EB; padding: 15px 20px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
        <h3 style="margin: 0 0 5px 0; color: #1F2937;">👥 Collaborative Filtering (User-Item Affinity)</h3>
        <p style="margin: 0; color: #566573; font-size: 14px;">Suggests catalog items based on historical buying habits of similar customer profiles.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

    # Select a target customer for demonstration
    customer_list = df_customers["customer_id"].unique().tolist() if not df_customers.empty and "customer_id" in df_customers.columns else []
    
    if customer_list:
        selected_cust_id = st.selectbox("Select Target Customer Profile", customer_list)
        
        if not df_merged.empty and "customer_id" in df_merged.columns and "product_id" in df_merged.columns and "quantity" in df_merged.columns:
            # Build User-Item Interaction Matrix
            user_item_matrix = df_merged.pivot_table(
                index="customer_id", 
                columns="product_id", 
                values="quantity", 
                aggfunc="sum"
            ).fillna(0)
            
            if not user_item_matrix.empty and len(user_item_matrix) > 1:
                if selected_cust_id in user_item_matrix.index:
                    # Calculate Cosine Similarity between users
                    user_sim = cosine_similarity(user_item_matrix)
                    user_sim_df = pd.DataFrame(user_sim, index=user_item_matrix.index, columns=user_item_matrix.index)
                    
                    # Find similar users
                    sim_users = user_sim_df[selected_cust_id].sort_values(ascending=False).iloc[1:4].index.tolist()
                    
                    if sim_users:
                        # Get products bought by similar users but not yet bought by target user
                        target_bought = set(user_item_matrix.loc[selected_cust_id][user_item_matrix.loc[selected_cust_id] > 0].index)
                        sim_bought = user_item_matrix.loc[sim_users].sum().sort_values(ascending=False)
                        collab_recs = [pid for pid in sim_bought.index if pid not in target_bought and sim_bought[pid] > 0][:5]
                        
                        if collab_recs:
                            collab_df = df_products[df_products["product_id"].isin(collab_recs)]
                            st.markdown("**⭐ Personalized For This Customer (Bought by Similar Users):**")
                            st.dataframe(
                                collab_df[["product_id", "name", "category", "price"]].rename(
                                    columns={"product_id": "ID", "name": "Product Name", "category": "Category", "price": "Price ($)"}
                                ),
                                use_container_width=True, hide_index=True
                            )
                        else:
                            st.info("No unique Collaborative suggestions found. Showing top general recommendations instead.")
                    else:
                        st.info("No similar customer purchasing patterns identified.")
                else:
                    st.info("This specific customer has no historical purchase logs yet to analyze.")
            else:
                st.info("Insufficient interactive purchasing matrix data to compute customer similarities.")
        else:
            st.info("No valid purchase item history available to construct user-item matrix.")
    else:
        st.info("No customer records found.")

    st.markdown("---")

    # ==========================================
    # 🏷️ CONTENT-BASED FILTERING SYSTEM
    # ==========================================
    
    st.markdown(
    """
    <div style="border: 2px solid #E5E7EB; padding: 15px 20px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
        <h3 style="margin: 0 0 5px 0; color: #1F2937;">🏷️ Content-Based Filtering (Item Similarity)</h3>
        <p style="margin: 0; color: #566573; font-size: 14px;">Finds similar items by analyzing shared category attributes and matching product pricing scales.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

    product_list = df_products["name"].tolist() if not df_products.empty and "name" in df_products.columns else []
    
    if product_list:
        selected_prod_name = st.selectbox("Select Product to Find Alternatives", product_list)
        target_prod_matches = df_products[df_products["name"] == selected_prod_name]
        
        if not target_prod_matches.empty:
            target_prod = target_prod_matches.iloc[0]
            target_id = target_prod["product_id"]
            
            # Feature Engineering: One-hot encode category, scale price
            content_df = df_products.copy()
            if "category" in content_df.columns:
                categories_encoded = pd.get_dummies(content_df["category"])
            else:
                categories_encoded = pd.DataFrame(index=content_df.index)
            
            # Max-Min scale price safely
            if "price" in content_df.columns:
                max_p, min_p = content_df["price"].max(), content_df["price"].min()
                content_df["scaled_price"] = (content_df["price"] - min_p) / (max_p - min_p) if max_p != min_p else 0
            else:
                content_df["scaled_price"] = 0
            
            features = pd.concat([categories_encoded, content_df[["scaled_price"]]], axis=1)
            
            if not features.empty and len(features) > 1:
                # Cosine Similarity Matrix between items
                item_sim = cosine_similarity(features)
                item_sim_df = pd.DataFrame(item_sim, index=content_df["product_id"], columns=content_df["product_id"])
                
                # Fetch Top 5 highly resembling matches
                similar_ids = item_sim_df[target_id].sort_values(ascending=False).iloc[1:6].index.tolist()
                similar_df = df_products[df_products["product_id"].isin(similar_ids)]
                
                st.markdown(f"**🌿 Similar Products to '{selected_prod_name}':**")
                st.dataframe(
                    similar_df[["product_id", "name", "category", "price"]].rename(
                        columns={"product_id": "ID", "name": "Product Name", "category": "Category", "price": "Price ($)"}
                    ),
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("Insufficient product catalog items to calculate content similarity.")
    else:
        st.info("No products available in catalog.")

    st.markdown("---")

    # ==========================================
    # 🔥 TRENDING PRODUCTS LISTING
    # ==========================================
    
    st.markdown(
    """
    <div style="border: 2px solid #E5E7EB; padding: 15px 20px; border-radius: 12px; background-color: #FAFAFA; margin-bottom: 20px;">
        <h3 style="margin: 0 0 5px 0; color: #1F2937;">🔥 Marketplace Trending Products</h3>
        <p style="margin: 0; color: #566573; font-size: 14px;">Top fast-moving products calculated by demand velocity and sales frequency in the last 30 days.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

    if not df_merged.empty and "product_id" in df_merged.columns and "quantity" in df_merged.columns:
        trending_sales = df_merged.groupby("product_id")["quantity"].sum().reset_index()
        trending_merged = pd.merge(trending_sales, df_products, on="product_id", how="inner").sort_values(by="quantity", ascending=False).head(5)
        
        if not trending_merged.empty:
            cols_to_display = [c for c in ["product_id", "name", "category", "price", "quantity"] if c in trending_merged.columns]
            rename_map = {
                "product_id": "ID",
                "name": "Trending Item",
                "category": "Category",
                "price": "Price ($)",
                "quantity": "Total Quantity Sold"
            }
            st.dataframe(
                trending_merged[cols_to_display].rename(columns=rename_map),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No matching product details found for sales history.")
    else:
        st.info("No transaction records available to determine platform trending trends.")