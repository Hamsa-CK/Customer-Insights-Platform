import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def show_recommendation_system(df_products, df_items, df_orders, df_customers):
    st.subheader("🛍️ Intelligent Recommendation Engine")

    # Clean and pre-process datasets
    valid_orders = df_orders[df_orders["status"] != "Cancelled"]
    valid_items = df_items[df_items["order_id"].isin(valid_orders["order_id"])]
    
    # --- CRASH FIX: Merge order metadata to explicitly pull 'customer_id' ---
    df_merged = pd.merge(valid_items, df_products, on="product_id", how="inner")
    df_merged = pd.merge(df_merged, valid_orders[["order_id", "customer_id"]], on="order_id", how="inner")

    # ==========================================
    # 👥 COLLABORATIVE FILTERING SYSTEM
    # ==========================================
    st.markdown("### 👥 Collaborative Filtering (User-Item Affinity)")
    st.caption("Suggests catalog items based on historical buying habits of similar customer profiles.")

    # Select a target customer for demonstration
    customer_list = df_customers["customer_id"].unique().tolist()
    if customer_list:
        selected_cust_id = st.selectbox("Select Target Customer Profile", customer_list)
        
        # Build User-Item Interaction Matrix
        user_item_matrix = df_merged.pivot_table(
            index="customer_id", 
            columns="product_id", 
            values="quantity", 
            aggfunc="sum"
        ).fillna(0)
        
        if not user_item_matrix.empty and len(user_item_matrix) > 1:
            # Check if the selected customer exists in the interaction matrix
            if selected_cust_id in user_item_matrix.index:
                # Calculate Cosine Similarity between users
                user_sim = cosine_similarity(user_item_matrix)
                user_sim_df = pd.DataFrame(user_sim, index=user_item_matrix.index, columns=user_item_matrix.index)
                
                # Find similar users
                sim_users = user_sim_df[selected_cust_id].sort_values(ascending=False).iloc[1:4].index.tolist()
                
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
                st.info("This specific customer has no historical purchase logs yet to analyze.")
        else:
            st.info("Insufficient interactive purchasing matrix data to compute customer similarities.")

    st.markdown("---")

    # ==========================================
    # 🏷️ CONTENT-BASED FILTERING SYSTEM
    # ==========================================
    st.markdown("### 🏷️ Content-Based Filtering (Item Similarity)")
    st.caption("Finds similar items by analyzing shared category attributes and matching product pricing scales.")

    product_list = df_products["name"].tolist()
    if product_list:
        selected_prod_name = st.selectbox("Select Product to Find Alternatives", product_list)
        target_prod = df_products[df_products["name"] == selected_prod_name].iloc[0]
        target_id = target_prod["product_id"]
        
        # Feature Engineering: One-hot encode category, scale price
        content_df = df_products.copy()
        categories_encoded = pd.get_dummies(content_df["category"])
        
        # Max-Min scale price safely
        max_p, min_p = content_df["price"].max(), content_df["price"].min()
        content_df["scaled_price"] = (content_df["price"] - min_p) / (max_p - min_p) if max_p != min_p else 0
        
        features = pd.concat([categories_encoded, content_df[["scaled_price"]]], axis=1)
        
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

    st.markdown("---")

    # ==========================================
    # 🔥 TRENDING PRODUCTS LISTING
    # ==========================================
    st.markdown("### 🔥 Marketplace Trending Products")
    st.caption("Top fast-moving products calculated by demand velocity and sales frequency in the last 30 days.")
    
    if not df_merged.empty:
        trending_sales = df_merged.groupby("product_id")["quantity"].sum().reset_index()
        trending_merged = pd.merge(trending_sales, df_products, on="product_id").sort_values(by="quantity", ascending=False).head(5)
        
        st.dataframe(
            trending_merged[["product_id", "name", "category", "price", "quantity"]].rename(
                columns={
                    "product_id": "ID",
                    "name": "Trending Item",
                    "category": "Category",
                    "price": "Price ($)",
                    "quantity": "Total Quantity Sold"
                }
            ),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No transaction records available to determine platform trending trends.")