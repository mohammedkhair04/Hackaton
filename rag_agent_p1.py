import sqlite3
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# --- Configuration from Phase 1 ---
DB_PATH = "/home/ubuntu/transactions.db"
TRANSACTIONS_TABLE_NAME = "transactions"
FAISS_INDEX_PATH = "/home/ubuntu/transaction_index.faiss"
FAISS_META_PATH = FAISS_INDEX_PATH + ".meta.csv"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
CLEANED_CSV_PATH = "/home/ubuntu/cleaned_jordan_transactions.csv" # For transaction details if needed

# --- Global Variables for Loaded Models/Data (to avoid reloading on every query) ---
faiss_index = None
sentence_model = None
faiss_id_map = None

def load_retrieval_components():
    """Loads FAISS index, sentence model, and transaction ID mapping."""
    global faiss_index, sentence_model, faiss_id_map
    print("--- Loading Retrieval Components ---")
    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"ERROR: FAISS index not found at {FAISS_INDEX_PATH}")
        return False
    if not os.path.exists(FAISS_META_PATH):
        print(f"ERROR: FAISS metadata not found at {FAISS_META_PATH}")
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
        # Assuming the CSV has 'faiss_index' (0 to n-1) and 'transaction_id'
        # We need a way to map FAISS's returned indices (which are 0 to n-1) to transaction_ids
        faiss_id_map = pd.Series(faiss_id_map_df["transaction_id"].values, index=faiss_id_map_df["faiss_index"].values)
        print(f"FAISS metadata loaded. Shape: {faiss_id_map.shape}")
        return True
    except Exception as e:
        print(f"Error loading retrieval components: {e}")
        return False

def semantic_search(query_text, k=5):
    """Performs semantic search using FAISS and returns relevant transaction IDs and scores."""
    global faiss_index, sentence_model, faiss_id_map
    if faiss_index is None or sentence_model is None or faiss_id_map is None:
        print("Retrieval components not loaded. Call load_retrieval_components() first.")
        if not load_retrieval_components():
            return []

    try:
        print(f"\nPerforming semantic search for query: 	'{query_text}	' with k={k}")
        query_embedding = sentence_model.encode([query_text])
        distances, indices = faiss_index.search(np.array(query_embedding).astype("float32"), k)
        
        results = []
        for i in range(len(indices[0])):
            faiss_result_idx = indices[0][i]
            distance = distances[0][i]
            if faiss_result_idx < len(faiss_id_map):
                transaction_id = faiss_id_map.iloc[faiss_result_idx] # Use .iloc for positional access if index is not 0-based int
                results.append({"transaction_id": transaction_id, "score": 1 - distance, "faiss_idx": faiss_result_idx}) # Convert distance to similarity score
            else:
                print(f"Warning: FAISS index {faiss_result_idx} out of bounds for faiss_id_map (len: {len(faiss_id_map)})")
        print(f"Semantic search results: {results}")
        return results
    except Exception as e:
        print(f"Error during semantic search: {e}")
        return []

def get_transaction_details_by_ids(transaction_ids):
    """Retrieves full transaction details from SQLite for a list of transaction IDs."""
    if not transaction_ids:
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(DB_PATH)
        # Create a placeholder string for the IN clause
        placeholders = ",".join(["?" for _ in transaction_ids])
        query = f"SELECT * FROM {TRANSACTIONS_TABLE_NAME} WHERE transaction_id IN ({placeholders})"
        df_details = pd.read_sql_query(query, conn, params=transaction_ids)
        conn.close()
        return df_details
    except Exception as e:
        print(f"Error getting transaction details from SQL: {e}")
        return pd.DataFrame()

# --- LangChain components will be added below ---
# For now, a simple test
if __name__ == "__main__":
    if load_retrieval_components():
        sample_query = "failed sales at Z Mall Al Bayader recently"
        semantic_results = semantic_search(sample_query, k=3)
        
        if semantic_results:
            retrieved_ids = [res["transaction_id"] for res in semantic_results]
            print(f"\nRetrieving details for IDs: {retrieved_ids}")
            details_df = get_transaction_details_by_ids(retrieved_ids)
            print("\nTransaction Details from SQL:")
            print(details_df)
    else:
        print("Failed to initialize retrieval components. Exiting.")

