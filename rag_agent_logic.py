import sqlite3
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# --- Configuration for Web App ---
# Adjust paths to be relative to the location of this script or an absolute path within the web app structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data") # Assuming data directory is one level up from src, then into data

DB_PATH = os.path.join(DATA_DIR, "transactions.db")
TRANSACTIONS_TABLE_NAME = "transactions"
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "transaction_index.faiss")
FAISS_META_PATH = FAISS_INDEX_PATH + ".meta.csv"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
# CLEANED_CSV_PATH = os.path.join(DATA_DIR, "cleaned_jordan_transactions.csv") # May not be needed if DB is primary source

# --- Global Variables for Loaded Models/Data (to avoid reloading on every query) ---
faiss_index = None
sentence_model = None
faiss_id_map = None
retrieval_components_loaded = False

def load_retrieval_components():
    """Loads FAISS index, sentence model, and transaction ID mapping."""
    global faiss_index, sentence_model, faiss_id_map, retrieval_components_loaded
    if retrieval_components_loaded:
        print("Retrieval components already loaded.")
        return True

    print("--- Loading Retrieval Components ---")
    print(f"Looking for DB at: {DB_PATH}")
    print(f"Looking for FAISS index at: {FAISS_INDEX_PATH}")
    print(f"Looking for FAISS meta at: {FAISS_META_PATH}")

    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"ERROR: FAISS index not found at {FAISS_INDEX_PATH}")
        return False
    if not os.path.exists(FAISS_META_PATH):
        print(f"ERROR: FAISS metadata not found at {FAISS_META_PATH}")
        return False
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return False

    try:
        print(f"Loading FAISS index from {FAISS_INDEX_PATH}...")
        faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        print(f"FAISS index loaded. Total vectors: {faiss_index.ntotal}")

        print(f"Loading Sentence Transformer model: {EMBEDDING_MODEL_NAME}...")
        sentence_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("Sentence Transformer model loaded.")

        print(f"Loading FAISS metadata (transaction IDs) from {FAISS_META_PATH}...")
        faiss_id_map_df = pd.read_csv(FAISS_META_PATH)
        faiss_id_map = pd.Series(faiss_id_map_df["transaction_id"].values, index=faiss_id_map_df["faiss_index"].values)
        print(f"FAISS metadata loaded. Shape: {faiss_id_map.shape}")
        retrieval_components_loaded = True
        return True
    except Exception as e:
        print(f"Error loading retrieval components: {e}")
        retrieval_components_loaded = False
        return False

def semantic_search(query_text, k=5):
    """Performs semantic search using FAISS and returns relevant transaction IDs and scores."""
    global faiss_index, sentence_model, faiss_id_map, retrieval_components_loaded
    if not retrieval_components_loaded:
        print("Retrieval components not loaded. Attempting to load now.")
        if not load_retrieval_components():
            return [], "Failed to load retrieval components."

    try:
        print(f"\nPerforming semantic search for query: '{query_text}' with k={k}")
        query_embedding = sentence_model.encode([query_text])
        distances, indices = faiss_index.search(np.array(query_embedding).astype("float32"), k)
        
        results = []
        for i in range(len(indices[0])):
            faiss_result_idx = indices[0][i]
            distance = distances[0][i]
            if faiss_result_idx >= 0 and faiss_result_idx < len(faiss_id_map):
                transaction_id = faiss_id_map.iloc[faiss_result_idx]
                results.append({"transaction_id": transaction_id, "score": 1 - distance, "faiss_idx": faiss_result_idx})
            else:
                print(f"Warning: FAISS index {faiss_result_idx} out of bounds for faiss_id_map (len: {len(faiss_id_map)})")
        print(f"Semantic search results: {results}")
        return results, None
    except Exception as e:
        error_message = f"Error during semantic search: {e}"
        print(error_message)
        return [], error_message

def get_transaction_details_by_ids(transaction_ids):
    """Retrieves full transaction details from SQLite for a list of transaction IDs."""
    if not transaction_ids:
        return pd.DataFrame(), "No transaction IDs provided."
    if not retrieval_components_loaded: # DB path check is part of this
        return pd.DataFrame(), "Retrieval components (including DB access) not ready."

    try:
        conn = sqlite3.connect(DB_PATH)
        placeholders = ",".join(["?" for _ in transaction_ids])
        query_sql = f"SELECT * FROM {TRANSACTIONS_TABLE_NAME} WHERE transaction_id IN ({placeholders})"
        df_details = pd.read_sql_query(query_sql, conn, params=transaction_ids)
        conn.close()
        if df_details.empty:
            return pd.DataFrame(), "No details found for the provided transaction IDs."
        return df_details, None
    except Exception as e:
        error_message = f"Error getting transaction details from SQL: {e}"
        print(error_message)
        return pd.DataFrame(), error_message

# Example usage (for direct script testing)
if __name__ == "__main__":
    if load_retrieval_components():
        sample_query = "failed sales at Z Mall Al Bayader recently"
        semantic_results, error = semantic_search(sample_query, k=3)
        
        if error:
            print(f"Search Error: {error}")
        elif semantic_results:
            retrieved_ids = [res["transaction_id"] for res in semantic_results]
            print(f"\nRetrieving details for IDs: {retrieved_ids}")
            details_df, error_details = get_transaction_details_by_ids(retrieved_ids)
            if error_details:
                print(f"Details Error: {error_details}")
            else:
                print("\nTransaction Details from SQL:")
                print(details_df)
    else:
        print("Failed to initialize retrieval components. Exiting.")

