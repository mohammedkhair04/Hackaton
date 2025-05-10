import pandas as pd
import sqlite3
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# --- Configuration ---
CLEANED_CSV_PATH = "cleaned_jordan_transactions.csv"
DB_PATH = "transactions.db"
TRANSACTIONS_TABLE_NAME = "transactions"
FAISS_INDEX_PATH = "transaction_index.faiss"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # A good default, relatively small and fast

def store_data_in_sql(df, db_path, table_name):
    """Stores the DataFrame into an SQLite database."""
    print(f"\n--- Task 1.3: Storing data in SQL Database ({db_path}) ---")
    try:
        conn = sqlite3.connect(db_path)
        # Ensure transaction_date is stored as TEXT in ISO format if it was datetime
        # The cleaned_df already has transaction_date_iso as string and transaction_date as datetime
        # For SQL, it's often easier to store dates as TEXT in ISO 8601 format or as Unix timestamps.
        # Let's use the transaction_date_iso column and rename transaction_date to avoid confusion if it's still datetime.
        df_for_sql = df.copy()
        if 'transaction_date' in df_for_sql.columns and pd.api.types.is_datetime64_any_dtype(df_for_sql['transaction_date']):
            # Drop the original datetime column if not needed, or ensure it's converted to text
            # df_for_sql.drop(columns=['transaction_date'], inplace=True)
            # Or convert it to text
            df_for_sql['transaction_date'] = df_for_sql['transaction_date'].astype(str)
            
        df_for_sql.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        print(f"Data successfully stored in SQLite table 	'{table_name}\' at {db_path}")
        # Verify by reading back a few rows
        conn = sqlite3.connect(db_path)
        sample_sql_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn)
        print("Sample data from SQL DB:")
        print(sample_sql_df)
        conn.close()
        return True
    except Exception as e:
        print(f"Error storing data in SQL: {e}")
        return False

def prepare_data_for_vectorization(df):
    """Prepares a textual representation for each transaction for embedding."""
    print("\n--- Task 1.4: Preparing data for vectorization ---")
    # Combine relevant text fields to create a meaningful sentence for each transaction
    # Example: "Sale transaction at Z Mall Al Bayader on 2025-04-20. Status: Failed. Amount: 2.05"
    # Adjust fields as per relevance for semantic search
    df['text_for_embedding'] = df.apply(
        lambda row: f"Transaction type: {row['transaction_type']}. Mall: {row['mall_name']}. Branch: {row['branch_name']}. Date: {row['transaction_date_iso']}. Status: {row['transaction_status']}. Amount: {row['transaction_amount']:.2f}. Tax: {row['tax_amount']:.2f}. ID: {row['transaction_id']}",
        axis=1
    )
    print("Created 'text_for_embedding' column.")
    print("Sample text for embedding:")
    print(df['text_for_embedding'].head(2).values)
    return df

def generate_embeddings_and_store_faiss(df, model_name, index_path):
    """Generates embeddings and stores them in a FAISS index."""
    print(f"\n--- Task 1.5: Generating embeddings with '{model_name}' and storing in FAISS ({index_path}) ---")
    if 'text_for_embedding' not in df.columns or df['text_for_embedding'].empty:
        print("Error: 'text_for_embedding' column is missing or empty. Cannot generate embeddings.")
        return False
    try:
        print(f"Loading sentence transformer model: {model_name}...")
        model = SentenceTransformer(model_name)
        
        texts_to_embed = df['text_for_embedding'].tolist()
        print(f"Generating embeddings for {len(texts_to_embed)} texts...")
        embeddings = model.encode(texts_to_embed, show_progress_bar=True)
        
        embedding_dim = embeddings.shape[1]
        print(f"Embeddings generated. Shape: {embeddings.shape}, Dimension: {embedding_dim}")
        
        # Build FAISS index
        index = faiss.IndexFlatL2(embedding_dim)  # Using L2 distance
        # For larger datasets, IndexIVFFlat might be better but requires training.
        # IndexIDMap allows mapping from FAISS index back to original IDs (e.g., DataFrame index or transaction_id)
        # Here, we'll use IndexFlatL2 for simplicity and store a separate mapping if needed.
        # Or, more robustly, use IndexIDMap to store original DataFrame indices
        # index = faiss.IndexIDMap(faiss.IndexFlatL2(embedding_dim))
        # index.add_with_ids(np.array(embeddings).astype('float32'), df.index.values.astype('int64'))

        index.add(np.array(embeddings).astype('float32'))
        print(f"FAISS index built. Total vectors in index: {index.ntotal}")
        
        faiss.write_index(index, index_path)
        print(f"FAISS index saved to {index_path}")
        # Also save the mapping from index to transaction_id for later retrieval
        # For simplicity, we can save the transaction_ids list in the order they were embedded.
        # A more robust way is to save df[['transaction_id']] or df.index to a file.
        df[['transaction_id']].to_csv(index_path + ".meta.csv", index_label="faiss_index")
        print(f"FAISS index metadata (transaction_ids) saved to {index_path + '.meta.csv'}")

        return True
    except Exception as e:
        print(f"Error generating/storing embeddings: {e}")
        return False

if __name__ == "__main__":
    if not os.path.exists(CLEANED_CSV_PATH):
        print(f"ERROR: Cleaned CSV file not found at {CLEANED_CSV_PATH}. Please run data_ingestion_p1.py first.")
    else:
        print(f"Loading cleaned data from {CLEANED_CSV_PATH}...")
        cleaned_df = pd.read_csv(CLEANED_CSV_PATH)
        
        if cleaned_df is not None and not cleaned_df.empty:
            # Task 1.3: Store in SQL
            sql_success = store_data_in_sql(cleaned_df, DB_PATH, TRANSACTIONS_TABLE_NAME)
            
            if sql_success:
                # Task 1.4: Prepare for vectorization
                df_for_embedding = prepare_data_for_vectorization(cleaned_df.copy()) # Use a copy
                
                # Task 1.5: Generate embeddings and store in FAISS
                faiss_success = generate_embeddings_and_store_faiss(df_for_embedding, EMBEDDING_MODEL_NAME, FAISS_INDEX_PATH)
                
                if faiss_success:
                    print("\n--- All Phase 1 Data Ingestion (Part 2) tasks completed successfully! ---")
                else:
                    print("\n--- Phase 1 Data Ingestion (Part 2) encountered errors during FAISS indexing. ---")
            else:
                print("\n--- Phase 1 Data Ingestion (Part 2) encountered errors during SQL storage. ---")
        else:
            print("Cleaned DataFrame is empty or None. Cannot proceed with SQL and FAISS storage.")

