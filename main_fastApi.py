import os
import sys
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd

# --- Add src to sys.path ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
# --- End sys.path modification ---

try:
    from src.advisor_logic import (
        load_all_models_once,
        semantic_search_transactions,
        get_transaction_details_by_ids_logic,
        load_data_from_sql_for_anomaly,
        detect_failed_transaction_anomaly_logic,
        detect_unusual_transaction_patterns_logic
    )
except ImportError as e:
    print(f"Critical Error: Could not import from advisor_logic.py: {e}")
    print(f"Please ensure 'advisor_logic.py' exists in the '{SRC_DIR}' directory and has no import errors itself.")
    print("Current sys.path:", sys.path)
    sys.exit(1)

app = FastAPI(title="Smart Financial Advisor API")

STATIC_DIR_PATH = os.path.join(PROJECT_ROOT, "static")
if not os.path.isdir(STATIC_DIR_PATH):
    print(f"Warning: Static directory not found at {STATIC_DIR_PATH}. The frontend (main.html) might not be served.")
else:
    app.mount("/static_assets", StaticFiles(directory=STATIC_DIR_PATH), name="static_assets")

models_initialized = False

@app.on_event("startup")
async def startup_event():
    global models_initialized
    print("FastAPI application startup: Attempting to load models...")
    if load_all_models_once():
        models_initialized = True
        print("Models loaded successfully.")
    else:
        models_initialized = False
        print("CRITICAL: Models failed to load during startup. Some endpoints may not function correctly.")

@app.get("/", response_class=HTMLResponse)
async def serve_main_html(request: Request): # Renamed function for clarity, optional
    """
    Serves the main main.html file from the 'static' directory.
    """
    html_file_path = os.path.join(STATIC_DIR_PATH, "main.html") # <<< CHANGED HERE
    if not os.path.exists(html_file_path):
        error_content = "<h1>Error 404: Not Found</h1><p>The main page (main.html) was not found.</p>" # <<< UPDATED ERROR MESSAGE
        return HTMLResponse(content=error_content, status_code=404)
    with open(html_file_path, "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.post("/query", response_class=JSONResponse)
async def handle_transaction_query_api(query_text: str = Form(...)):
    if not models_initialized:
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: Models are not initialized. Please try again shortly."
        )
    if not query_text or not query_text.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
    try:
        semantic_results, search_error = semantic_search_transactions(query_text, k=5)
        if search_error:
            print(f"Error during semantic search: {search_error}")
            raise HTTPException(status_code=500, detail=f"Error during semantic search: {search_error}")
        if not semantic_results:
            return JSONResponse(content={"message": "No relevant transactions found for your query."})
        retrieved_ids = [res["transaction_id"] for res in semantic_results]
        details_df, details_error = get_transaction_details_by_ids_logic(retrieved_ids)
        if details_error:
            print(f"Error fetching transaction details: {details_error}")
            raise HTTPException(status_code=500, detail=f"Error fetching transaction details: {details_error}")
        transactions_details = details_df.to_dict(orient="records")
        score_map = {res["transaction_id"]: res["score"] for res in semantic_results}
        for detail in transactions_details:
            detail["semantic_score"] = score_map.get(detail["transaction_id"])
        transactions_details.sort(key=lambda x: x.get("semantic_score", 0) or 0, reverse=True)
        return JSONResponse(content={"transactions": transactions_details})
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /query endpoint: {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal server error occurred.")

@app.post("/run_anomaly_detection", response_class=JSONResponse)
async def run_anomaly_detection_workflows_api():
    if not models_initialized:
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: Models are not initialized. Please try again shortly."
        )
    results_payload = {
        "anomaly_results": [],
        "unusual_transactions": []
    }
    try:
        transaction_df, load_error = load_data_from_sql_for_anomaly()
        if load_error:
            print(f"Error loading data for anomaly detection: {load_error}")
            raise HTTPException(status_code=500, detail=f"Failed to load data for anomaly detection: {load_error}")
        if transaction_df is None or transaction_df.empty:
            return JSONResponse(content=results_payload)
        is_failed_anomaly, failed_message, _ = detect_failed_transaction_anomaly_logic(
            transaction_df.copy(),
            mall_name="Z Mall",
            time_window_hours=7*24,
            failure_threshold_percentage=10
        )
        results_payload["anomaly_results"].append({
            "workflow": "Failed Transaction Rate (Z Mall, last 7 days, >10%)", 
            "status": "ALERT" if is_failed_anomaly else "Normal", 
            "message": failed_message
        })
        unusual_amounts_df, unusual_message = detect_unusual_transaction_patterns_logic(
            transaction_df.copy(),
            amount_std_dev_multiplier=2.5
        )
        results_payload["anomaly_results"].append({
            "workflow": "Unusual Transaction Amounts (Overall, >2.5 Std Dev)", 
            "status": "ALERT" if not unusual_amounts_df.empty else "Normal", 
            "message": unusual_message
        })
        if not unusual_amounts_df.empty:
            if 'transaction_date' in unusual_amounts_df.columns and 'transaction_date_iso' not in unusual_amounts_df.columns:
                 if pd.api.types.is_datetime64_any_dtype(unusual_amounts_df['transaction_date']):
                    unusual_amounts_df['transaction_date_iso'] = unusual_amounts_df['transaction_date'].apply(lambda x: x.isoformat() if pd.notnull(x) else None)
                 else:
                    unusual_amounts_df.rename(columns={'transaction_date': 'transaction_date_iso'}, inplace=True)
            cols_for_frontend = ['transaction_id', 'mall_name', 'branch_name', 'transaction_date_iso', 'transaction_amount', 'transaction_status']
            existing_cols = [col for col in cols_for_frontend if col in unusual_amounts_df.columns]
            results_payload["unusual_transactions"] = unusual_amounts_df[existing_cols].to_dict(orient="records")
        return JSONResponse(content=results_payload)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /run_anomaly_detection endpoint: {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal server error occurred during anomaly detection.")
# ... (startup_event where models_initialized is set) ...

@app.post("/query", response_class=JSONResponse)
async def handle_transaction_query_api(query_text: str = Form(...)):
    if not models_initialized:  # <<< THIS IS THE KEY CHECK
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: Models are not initialized. Please try again shortly."
        )
    # ... rest of the query logic ...

@app.post("/run_anomaly_detection", response_class=JSONResponse)
async def run_anomaly_detection_workflows_api():
    if not models_initialized: # <<< THIS IS THE KEY CHECK
        raise HTTPException(
            status_code=503, 
            detail="Service Unavailable: Models are not initialized. Please try again shortly."
        )
    # ... rest of the anomaly logic ...
if __name__ == "__main__":
    print("This is a FastAPI application. To run it, use Uvicorn:")
    print("Example: uvicorn main_fastapi:app --reload --host 0.0.0.0 --port 8000")
    print(f"Ensure 'advisor_logic.py' is in the '{SRC_DIR}' directory.")
    print(f"Ensure 'main.html' (not index.html) is in the '{STATIC_DIR_PATH}' directory.")