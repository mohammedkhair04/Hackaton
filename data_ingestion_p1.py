import pandas as pd
import os

def load_and_clean_data(csv_path):
    # Task 1.1: Load CSV Data
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded {csv_path}. Shape: {df.shape}")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

    # Task 1.2: Clean and Normalize Data
    print("Starting data cleaning and normalization...")
    
    # Drop rows with missing critical transaction_id
    df.dropna(subset=["transaction_id"], inplace=True)
    print(f"Shape after dropping NA transaction_id: {df.shape}")
    
    # Ensure transaction_amount is numeric and filter out non-positive amounts
    df["transaction_amount"] = pd.to_numeric(df["transaction_amount"], errors='coerce')
    df.dropna(subset=["transaction_amount"], inplace=True) # Drop rows where conversion failed
    df = df[df["transaction_amount"] > 0]
    print(f"Shape after filtering non-positive transaction_amount: {df.shape}")

    # Convert transaction_date to datetime objects and then to ISO format
    # Original format in CSV: DD/MM/YYYY HH:MM
    try:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], format='%d/%m/%Y %H:%M', errors='coerce')
        df.dropna(subset=["transaction_date"], inplace=True) # Drop rows where date conversion failed
        df["transaction_date_iso"] = df["transaction_date"].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
        print("Converted 'transaction_date' to ISO format.")
    except Exception as e:
        print(f"Error converting transaction_date: {e}")

    # Ensure tax_amount is numeric
    df["tax_amount"] = pd.to_numeric(df["tax_amount"], errors='coerce')
    # Fill NA tax_amount with 0 after coercion, as tax can be 0
    df["tax_amount"].fillna(0, inplace=True)
    print("Processed 'tax_amount'.")

    print(f"Cleaned data shape: {df.shape}")
    print("Sample of cleaned data:")
    print(df.head())
    print("Info of cleaned data:")
    df.info()

    return df

if __name__ == "__main__":
    # Use the restored file path
    csv_file_path = "/home/ubuntu/upload/.recovery/jordan_transactions.csv"
    # Output path for the cleaned file
    cleaned_csv_path = "/home/ubuntu/cleaned_jordan_transactions.csv"

    if not os.path.exists(csv_file_path):
        print(f"ERROR: Input CSV file not found at {csv_file_path}")
    else:
        cleaned_df = load_and_clean_data(csv_file_path)
        
        if cleaned_df is not None and not cleaned_df.empty:
            try:
                cleaned_df.to_csv(cleaned_csv_path, index=False)
                print(f"Cleaned data saved to {cleaned_csv_path}")
            except Exception as e:
                print(f"Error saving cleaned data to CSV: {e}")
        elif cleaned_df is not None and cleaned_df.empty:
            print("Warning: Cleaned DataFrame is empty. No data saved.")
        else:
            print("Cleaned DataFrame is None. No data saved.")

