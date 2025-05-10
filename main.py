import sys
import os
sys.path.append(r"C:\Users\Mohammed\OneDrive - UNIVERSITY OF PETRA\Desktop\AI_Agent\New folder\Comprehensive Deployment Guide for Smart Financial Advisor Website")

from flask import Flask, render_template, request, jsonify
import pandas as pd

# Import the core logic
from src.advisor_logic import (
    load_all_models_once,
    semantic_search_transactions,
    get_transaction_details_by_ids_logic,
    load_data_from_sql_for_anomaly,
    detect_failed_transaction_anomaly_logic,
    detect_unusual_transaction_patterns_logic
)

# Create Flask app
app = Flask(__name__, static_folder="static", template_folder="static")
app.config["SECRET_KEY"] = os.urandom(24)

# Global variable to track if models are loaded
models_initialized = False

@app.before_request
def initialize_models():
    """Load models before the first request that needs them."""
    global models_initialized
    if not models_initialized:
        print("Attempting to load models for the first time...")
        if load_all_models_once():
            models_initialized = True
            print("Models loaded successfully.")
        else:
            print("CRITICAL: Models failed to load. Application might not function correctly.")

@app.route("/")
def index():
    """Serves the main HTML page."""
    return render_template("main.html")

@app.route("/query", methods=["POST"])
def handle_query():
    """Handles user queries for transaction insights."""
    if not models_initialized:
        return render_template("main.html", query_error="Models are not initialized. Please try again shortly or contact support.")

    query_text = request.form.get("query_text")
    if not query_text:
        return render_template("main.html", query_error="Please enter a query.")

    try:
        # 1. Perform semantic search
        semantic_results, error = semantic_search_transactions(query_text, k=5)
        if error:
            return render_template("main.html", query_text=query_text, query_error=error)
        
        if not semantic_results:
            return render_template("main.html", query_text=query_text, query_message="No relevant transactions found for your query.")

        # 2. Get details for retrieved IDs
        retrieved_ids = [res["transaction_id"] for res in semantic_results]
        details_df, error = get_transaction_details_by_ids_logic(retrieved_ids)
        if error:
            return render_template("main.html", query_text=query_text, query_error=error)

        # Convert DataFrame to list of dicts for easy rendering in template
        transactions_details = details_df.to_dict(orient="records")
        
        # Add semantic search scores to the details for display
        score_map = {res["transaction_id"]: res["score"] for res in semantic_results}
        for detail in transactions_details:
            detail["semantic_score"] = score_map.get(detail["transaction_id"], "N/A")
        
        # Sort by score descending before rendering
        transactions_details.sort(key=lambda x: x.get("semantic_score", 0), reverse=True)

        return render_template("main.html", query_text=query_text, transactions=transactions_details)

    except Exception as e:
        print(f"Error in /query: {e}")
        return render_template("main.html", query_text=query_text, query_error=f"An unexpected error occurred: {str(e)}")

@app.route("/run_anomaly_detection", methods=["POST"])
def run_anomaly_detection():
    """Runs the anomaly detection workflows."""
    if not models_initialized:
        return render_template("main.html", anomaly_error="Models are not initialized. Please try again shortly or contact support.")

    results = []
    try:
        # Load data for anomaly detection
        transaction_df, error = load_data_from_sql_for_anomaly()
        if error:
            return render_template("main.html", anomaly_error=error)
        if transaction_df is None:
            return render_template("main.html", anomaly_error="Could not load transaction data for anomaly detection.")

        # 1. Detect failed transaction anomaly (example for Z Mall)
        is_failed_anomaly, failed_message, failed_tx_ids = detect_failed_transaction_anomaly_logic(
            transaction_df.copy(), 
            mall_name="Z Mall", 
            time_window_hours=7*24, 
            failure_threshold_percentage=10
        )
        results.append({
            "workflow": "Failed Transaction Rate (Z Mall, last 7 days, >10%)", 
            "status": "ALERT" if is_failed_anomaly else "Normal", 
            "message": failed_message
        })
        
        # 2. Detect unusual transaction patterns
        unusual_amounts_df, unusual_message = detect_unusual_transaction_patterns_logic(
            transaction_df.copy(), 
            amount_std_dev_multiplier=2.5
        )
        status_unusual = "ALERT" if not unusual_amounts_df.empty else "Normal"
        results.append({
            "workflow": "Unusual Transaction Amounts (Overall, >2.5 Std Dev)", 
            "status": status_unusual, 
            "message": unusual_message
        })
        
        # Prepare details of anomalous transactions for display
        anomalous_transactions_display = []
        if not unusual_amounts_df.empty:
            anomalous_transactions_display = unusual_amounts_df.to_dict(orient="records")

        return render_template("main.html", anomaly_results=results, unusual_transactions=anomalous_transactions_display)

    except Exception as e:
        print(f"Error in /run_anomaly_detection: {e}")
        return render_template("main.html", anomaly_error=f"An unexpected error occurred during anomaly detection: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)