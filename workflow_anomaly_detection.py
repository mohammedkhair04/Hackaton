import pandas as pd
import sqlite3

DB_PATH = "transactions.db"
TRANSACTIONS_TABLE_NAME = "transactions"
CLEANED_CSV_PATH = "cleaned_jordan_transactions.csv"

def load_data_from_sql(db_path, table_name):
    """Loads transaction data from the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        # Convert relevant columns to appropriate types if they aren't already
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        if 'transaction_amount' in df.columns:
            df['transaction_amount'] = pd.to_numeric(df['transaction_amount'])
        print(f"Successfully loaded data from SQL. Shape: {df.shape}")
        return df
    except Exception as e:
        print(f"Error loading data from SQL: {e}")
        # Fallback to CSV if SQL fails, though ideally SQL should be the source
        try:
            print(f"Falling back to loading from CSV: {CLEANED_CSV_PATH}")
            df = pd.read_csv(CLEANED_CSV_PATH)
            if 'transaction_date' in df.columns:
                 df['transaction_date'] = pd.to_datetime(df['transaction_date'])
            if 'transaction_amount' in df.columns:
                df['transaction_amount'] = pd.to_numeric(df['transaction_amount'])
            print(f"Successfully loaded data from CSV. Shape: {df.shape}")
            return df
        except Exception as e_csv:
            print(f"Error loading data from CSV as fallback: {e_csv}")
            return None

def detect_failed_transaction_anomaly(df, mall_name, time_window_hours=24, failure_threshold_percentage=50):
    """Detects anomaly if failed transactions for a specific mall exceed a threshold in a time window."""
    print(f"\n--- Anomaly Detection: High Failed Transactions for {mall_name} ---")
    if df is None or df.empty:
        print("No data to analyze.")
        return False, "No data"

    # Filter for the specific mall and recent transactions
    # Assuming 'transaction_date' is already datetime objects
    recent_time_cutoff = pd.Timestamp.now() - pd.Timedelta(hours=time_window_hours)
    mall_df = df[(df['mall_name'] == mall_name) & (df['transaction_date'] >= recent_time_cutoff)]

    if mall_df.empty:
        print(f"No recent transactions found for {mall_name} in the last {time_window_hours} hours.")
        return False, f"No recent transactions for {mall_name}"

    total_transactions = len(mall_df)
    failed_transactions = len(mall_df[mall_df['transaction_status'] == 'Failed'])
    
    if total_transactions == 0: # Should be caught by mall_df.empty but as a safeguard
        failure_rate = 0
    else:
        failure_rate = (failed_transactions / total_transactions) * 100

    print(f"Mall: {mall_name}, Time Window: {time_window_hours}hrs")
    print(f"Total Transactions: {total_transactions}, Failed Transactions: {failed_transactions}")
    print(f"Failure Rate: {failure_rate:.2f}%")

    if failure_rate >= failure_threshold_percentage:
        alert_message = f"ALERT: High failed transaction rate for {mall_name}! {failure_rate:.2f}% failed in the last {time_window_hours} hours ({failed_transactions}/{total_transactions})."
        print(alert_message)
        return True, alert_message
    else:
        print(f"Failure rate for {mall_name} ({failure_rate:.2f}%) is below threshold ({failure_threshold_percentage}%).")
        return False, f"Normal failure rate for {mall_name}"

def detect_unusual_transaction_patterns(df, amount_std_dev_multiplier=3):
    """Detects transactions with amounts significantly deviating from the mean."""
    print(f"\n--- Anomaly Detection: Unusual Transaction Amounts (Std Dev Multiplier: {amount_std_dev_multiplier}) ---")
    if df is None or df.empty or 'transaction_amount' not in df.columns:
        print("No data or transaction_amount column to analyze.")
        return pd.DataFrame()

    mean_amount = df['transaction_amount'].mean()
    std_amount = df['transaction_amount'].std()
    
    upper_bound = mean_amount + (amount_std_dev_multiplier * std_amount)
    lower_bound = mean_amount - (amount_std_dev_multiplier * std_amount)
    # Amounts are positive, so lower bound effectively min(0, calculated_lower_bound) if needed, but usually not for positive values.
    lower_bound = max(0, lower_bound) # Ensure lower bound is not negative for amounts

    print(f"Mean Transaction Amount: {mean_amount:.2f}")
    print(f"Std Dev Transaction Amount: {std_amount:.2f}")
    print(f"Anomaly Bounds for Amount: ({lower_bound:.2f}, {upper_bound:.2f})")

    anomalous_transactions = df[
        (df['transaction_amount'] > upper_bound) |
        (df['transaction_amount'] < lower_bound)
    ]

    if not anomalous_transactions.empty:
        print(f"Found {len(anomalous_transactions)} transactions with unusual amounts:")
        print(anomalous_transactions[['transaction_id', 'mall_name', 'branch_name', 'transaction_date', 'transaction_amount', 'transaction_status']])
    else:
        print("No transactions with amounts significantly deviating from the mean found.")
    
    return anomalous_transactions

if __name__ == "__main__":
    transaction_df = load_data_from_sql(DB_PATH, TRANSACTIONS_TABLE_NAME)

    if transaction_df is not None:
        # Example 1: Check for high failed transactions at Z Mall
        is_failed_anomaly, failed_message = detect_failed_transaction_anomaly(transaction_df, mall_name="Z Mall", time_window_hours=7*24, failure_threshold_percentage=10)
        # Note: Using 7*24 hours to likely get some data given the dataset's date range.
        # For a real-time system, time_window_hours would be much smaller (e.g., 1, 6, 24).

        # Example 2: Detect unusual transaction amounts across all data
        unusual_amounts_df = detect_unusual_transaction_patterns(transaction_df, amount_std_dev_multiplier=2.5)

        # Simulate sending alerts (in a real system, this would integrate with notification services)
        if is_failed_anomaly:
            print(f"\nWORKFLOW_ALERT_SIMULATION (Failed Transactions): {failed_message}")
        
        if not unusual_amounts_df.empty:
            print(f"\nWORKFLOW_ALERT_SIMULATION (Unusual Amounts): Found {len(unusual_amounts_df)} transactions with unusual amounts. Details logged above.")
    else:
        print("Could not load transaction data for anomaly detection.")

