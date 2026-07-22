import pandas as pd
import os

def delete_vendor_by_email(email_to_delete):
    users_path = "data/users.parquet"
    vendors_path = "data/vendors.parquet"
    
    if not os.path.exists(users_path) or not os.path.exists(vendors_path):
        print("❌ Error: Parquet files not found. Make sure you are running this in your project root.")
        return

    # 1. Load the current datasets
    df_users = pd.read_parquet(users_path)
    df_vendors = pd.read_parquet(vendors_path)
    
    # 2. Find the user ID matching the targeted email
    target_user = df_users[df_users["email"] == email_to_delete]
    
    if target_user.empty:
        print(f"❓ No account found with the email: {email_to_delete}")
        return
        
    user_id_to_remove = target_user.iloc[0]["user_id"]
    
    # 3. Filter out the vendor records from both DataFrames
    df_users_cleaned = df_users[df_users["email"] != email_to_delete]
    df_vendors_cleaned = df_vendors[df_vendors["user_id"] != user_id_to_remove]
    
    # 4. Save the cleaned DataFrames back to disk
    df_users_cleaned.to_parquet(users_path, index=False)
    df_vendors_cleaned.to_parquet(vendors_path, index=False)
    
    print(f"🗑️ Successfully deleted vendor '{email_to_delete}' (User ID: {user_id_to_remove}) from datasets.")

# --- RUN THE CLEANUP ---
# Change this to the exact email you used for VoltDrive Logistics
TARGET_EMAIL = "partner@shopsense.com" 
delete_vendor_by_email(TARGET_EMAIL)