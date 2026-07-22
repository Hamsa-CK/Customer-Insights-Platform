import pandas as pd
import uuid

def seed_vendor_marketplace_data(target_vendor_id):
    """
    Clones existing marketplace records from the dataset templates 
    and assigns them directly to the newly approved vendor ID.
    """
    try:
        # 1. Load all operational Parquet files
        df_products = pd.read_parquet("data/products.parquet")
        df_items = pd.read_parquet("data/order_items.parquet")
        df_orders = pd.read_parquet("data/orders.parquet")
        df_reviews = pd.read_parquet("data/reviews.parquet")
        df_customers = pd.read_parquet("data/customers.parquet")
        df_users = pd.read_parquet("data/users.parquet")
        
        # 2. Safety check: Ensure there is sample data to borrow from
        if df_products.empty or df_items.empty:
            return False, "Base datasets are empty. Cannot extract sample data templates."

        # 3. Step 1: Clone 3-5 existing products for this new vendor
        sample_size = min(4, len(df_products))
        sampled_products = df_products.sample(n=sample_size).copy()
        
        # Give them new unique product IDs but map them to our target vendor
        product_id_mapping = {}
        new_products_rows = []
        
        for _, row in sampled_products.iterrows():
            old_id = row["product_id"]
            new_id = f"PROD_{uuid.uuid4().hex[:4].upper()}"
            product_id_mapping[old_id] = new_id
            
            new_prod = row.to_dict()
            new_prod["product_id"] = new_id
            new_prod["vendor_id"] = target_vendor_id  # Ownership transfer
            new_products_rows.append(new_prod)
            
        df_new_products = pd.DataFrame(new_products_rows)
        df_products = pd.concat([df_products, df_new_products], ignore_index=True)

        # 4. Step 2: Clone historical Order Items matching those sampled products
        sampled_items = df_items[df_items["product_id"].isin(product_id_mapping.keys())].copy()
        new_items_rows = []
        order_id_mapping = {}
        
        for _, row in sampled_items.iterrows():
            old_order_id = row["order_id"]
            if old_order_id not in order_id_mapping:
                order_id_mapping[old_order_id] = f"ORD_{uuid.uuid4().hex[:6].upper()}"
                
            new_item = row.to_dict()
            new_item["order_item_id"] = f"ITEM_{uuid.uuid4().hex[:4].upper()}"
            new_item["order_id"] = order_id_mapping[old_order_id]
            new_item["product_id"] = product_id_mapping[row["product_id"]]
            new_items_rows.append(new_item)
            
        df_new_items = pd.DataFrame(new_items_rows)
        df_items = pd.concat([df_items, df_new_items], ignore_index=True)

        # 5. Step 3: Clone master Orders matching the cloned items
        sampled_orders = df_orders[df_orders["order_id"].isin(order_id_mapping.keys())].copy()
        new_orders_rows = []
        
        for _, row in sampled_orders.iterrows():
            new_order = row.to_dict()
            new_order["order_id"] = order_id_mapping[row["order_id"]]
            new_orders_rows.append(new_order)
            
        df_new_orders = pd.DataFrame(new_orders_rows)
        df_orders = pd.concat([df_orders, df_new_orders], ignore_index=True)

        # 6. Step 4: Clone Reviews matching the new products
        sampled_reviews = df_reviews[df_reviews["product_id"].isin(product_id_mapping.keys())].copy()
        new_reviews_rows = []
        
        for _, row in sampled_reviews.iterrows():
            new_rev = row.to_dict()
            new_rev["review_id"] = f"REV_{uuid.uuid4().hex[:4].upper()}"
            new_rev["product_id"] = product_id_mapping[row["product_id"]]
            new_reviews_rows.append(new_rev)
            
        if new_reviews_rows:
            df_reviews = pd.concat([df_reviews, pd.DataFrame(new_reviews_rows)], ignore_index=True)

        # 7. Write everything back safely into Parquet storage
        df_products.to_parquet("data/products.parquet")
        df_items.to_parquet("data/order_items.parquet")
        df_orders.to_parquet("data/orders.parquet")
        df_reviews.to_parquet("data/reviews.parquet")
        
        return True, "Success"
        
    except Exception as e:
        return False, str(e)