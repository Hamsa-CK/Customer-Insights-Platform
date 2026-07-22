import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def generate_datasets():
    print("⏳ Generating highly structured e-commerce datasets...")
    
    # 1. Generate 501 Users (1 Admin + 500 Customers) + 100 Vendors
    users_list = [{
        "user_id": 1,
        "email": "admin@shopsense.com",
        "password": "admin",
        "role": "admin"
    }]
    
    # 2. Generate 100 Vendors
    vendors_list = []
    for i in range(1, 101):
        v_user_id = 1 + i
        users_list.append({
            "user_id": v_user_id,
            "email": f"vendor{i}@shopsense.com",
            "password": "password123",
            "role": "vendor"
        })
        vendors_list.append({
            "vendor_id": i,
            "user_id": v_user_id,
            "business_name": fake.company(),
            "owner_name": fake.name(),
            "phone": fake.phone_number()[:15],
            "gst_number": f"{random.randint(10,99)}ABCDE{random.randint(1000,9999)}F{random.randint(1,9)}Z{random.randint(1,9)}",
            "address": fake.street_address(),
            "city": fake.city(),
            "state": fake.state(),
            "commission_percentage": 10.0,
            "status": random.choice(["Active", "Active", "Active", "Pending", "Suspended"])
        })
    
    # 3. Generate 500 Customers
    customers_list = []
    for i in range(1, 501):
        c_user_id = 101 + i
        users_list.append({
            "user_id": c_user_id,
            "email": f"customer{i}@shopsense.com",
            "password": "password123",
            "role": "customer"
        })
        customers_list.append({
            "customer_id": i,
            "user_id": c_user_id,
            "name": fake.name(),
            "phone": fake.phone_number()[:15]
        })
        
    # 4. Generate 1000 Products
    categories = ["Electronics", "Fashion", "Home & Living", "Beauty", "Sports", "Books", "Automotive", "Toys", "Groceries", "Health"]
    products_list = []
    for i in range(1, 1001):
        v_id = random.randint(1, 100)
        price = round(random.uniform(10.0, 1500.0), 2)
        products_list.append({
            "product_id": i,
            "vendor_id": v_id,
            "category": random.choice(categories),
            "name": f"{fake.color_name()} {fake.word().capitalize()} {random.choice(['Pro', 'Max', 'Ultra', 'Plus', 'Lite', 'Classic'])}",
            "description": fake.sentence(nb_words=10),
            "price": price,
            "current_stock": random.randint(0, 250),
            "low_stock_threshold": random.randint(5, 20)
        })

    df_vendors = pd.DataFrame(vendors_list)
    df_products = pd.DataFrame(products_list)
    df_customers = pd.DataFrame(customers_list)

    # 5. Generate 20,000 Order Records
    orders_list = []
    order_items_list = []
    base_date = datetime(2025, 7, 16)

    for i in range(1, 20001):
        cust_id = random.randint(1, 500)
        num_items = random.randint(1, 4)
        order_date = base_date + timedelta(
            days=random.randint(0, 364),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        total_amount = 0.0
        for _ in range(num_items):
            prod = df_products.sample(n=1).iloc[0]
            qty = random.randint(1, 3)
            subtotal = round(float(prod['price']) * qty, 2)
            total_amount += subtotal
            
            order_items_list.append({
                "order_id": i,
                "product_id": int(prod['product_id']),
                "vendor_id": int(prod['vendor_id']),
                "quantity": qty,
                "price_per_unit": float(prod['price'])
            })
            
        orders_list.append({
            "order_id": i,
            "customer_id": cust_id,
            "total_amount": round(total_amount, 2),
            "status": random.choice(["Delivered", "Delivered", "Delivered", "Shipped", "Pending", "Cancelled"]),
            "created_at": order_date
        })

    # 6. Generate 5000 Customer Reviews
    reviews_list = []
    for i in range(1, 5001):
        cust_id = random.randint(1, 500)
        prod_id = random.randint(1, 1000)
        reviews_list.append({
            "review_id": i,
            "customer_id": cust_id,
            "product_id": prod_id,
            "rating": random.choice([5, 5, 4, 4, 3, 2, 1]),
            "comment": fake.paragraph(nb_sentences=1),
            "created_at": base_date + timedelta(days=random.randint(100, 364))
        })

    pd.DataFrame(users_list).to_parquet(f"{DATA_DIR}/users.parquet", index=False)
    df_vendors.to_parquet(f"{DATA_DIR}/vendors.parquet", index=False)
    df_products.to_parquet(f"{DATA_DIR}/products.parquet", index=False)
    df_customers.to_parquet(f"{DATA_DIR}/customers.parquet", index=False)
    pd.DataFrame(orders_list).to_parquet(f"{DATA_DIR}/orders.parquet", index=False)
    pd.DataFrame(order_items_list).to_parquet(f"{DATA_DIR}/order_items.parquet", index=False)
    pd.DataFrame(reviews_list).to_parquet(f"{DATA_DIR}/reviews.parquet", index=False)
    
    print("✅ All Baseline Datasets generated successfully!")

# 🚨 NEW: Seed data helper for newly approved vendor profile creation
def seed_vendor_marketplace_data(vendor_id):
    vendor_id = int(vendor_id)
    
    df_products = pd.read_parquet(f"{DATA_DIR}/products.parquet")
    df_orders = pd.read_parquet(f"{DATA_DIR}/orders.parquet")
    df_items = pd.read_parquet(f"{DATA_DIR}/order_items.parquet")
    df_reviews = pd.read_parquet(f"{DATA_DIR}/reviews.parquet")
    
    # 1. Create mock store products
    categories = ["Electronics", "Fashion", "Home & Living", "Beauty", "Sports"]
    new_products = []
    start_prod_id = int(df_products["product_id"].max() + 1)
    
    for idx in range(10):  # List 10 default sample products
        new_products.append({
            "product_id": start_prod_id + idx,
            "vendor_id": vendor_id,
            "category": random.choice(categories),
            "name": f"{fake.color_name()} {fake.word().capitalize()} Enterprise",
            "description": fake.sentence(nb_words=8),
            "price": round(random.uniform(40.0, 600.0), 2),
            "current_stock": random.randint(50, 200),
            "low_stock_threshold": 10
        })
    df_new_prods = pd.DataFrame(new_products)
    df_products = pd.concat([df_products, df_new_prods], ignore_index=True)
    df_products.to_parquet(f"{DATA_DIR}/products.parquet", index=False)
    
    # 2. Backfill transactional sales records
    start_order_id = int(df_orders["order_id"].max() + 1)
    start_review_id = int(df_reviews["review_id"].max() + 1)
    base_date = datetime(2025, 7, 16)
    
    new_orders = []
    new_items = []
    new_revs = []
    
    for idx in range(45):  # Add 45 historical marketplace transaction orders
        o_id = start_order_id + idx
        c_id = random.randint(1, 500)
        o_date = base_date + timedelta(days=random.randint(0, 350), hours=random.randint(0, 23))
        
        chosen_prod = df_new_prods.sample(n=1).iloc[0]
        qty = random.randint(1, 2)
        subtotal = round(float(chosen_prod['price']) * qty, 2)
        
        new_items.append({
            "order_id": o_id,
            "product_id": int(chosen_prod['product_id']),
            "vendor_id": vendor_id,
            "quantity": qty,
            "price_per_unit": float(chosen_prod['price'])
        })
        
        new_orders.append({
            "order_id": o_id,
            "customer_id": c_id,
            "total_amount": subtotal,
            "status": "Delivered",
            "created_at": o_date
        })
        
        # Add feedback record loop
        if random.random() > 0.6:
            new_revs.append({
                "review_id": start_review_id + len(new_revs),
                "customer_id": c_id,
                "product_id": int(chosen_prod['product_id']),
                "rating": random.choice([4, 5]),
                "comment": "Fast shipping, great quality structure!",
                "created_at": o_date + timedelta(days=3)
            })
            
    pd.concat([df_orders, pd.DataFrame(new_orders)], ignore_index=True).to_parquet(f"{DATA_DIR}/orders.parquet", index=False)
    pd.concat([df_items, pd.DataFrame(new_items)], ignore_index=True).to_parquet(f"{DATA_DIR}/order_items.parquet", index=False)
    if new_revs:
        pd.concat([df_reviews, pd.DataFrame(new_revs)], ignore_index=True).to_parquet(f"{DATA_DIR}/reviews.parquet", index=False)
        
    print(f"🎯 Successfully seeded historical metrics records for Vendor {vendor_id}!")

if __name__ == "__main__":
    generate_datasets()