# Demo Script Outline: Smart Financial Advisor (2-3 Minutes)

**Objective**: Showcase the core functionalities of the Smart Financial Advisor, including data ingestion, natural language querying (semantic search + SQL retrieval), and autonomous anomaly detection.

**Target Audience**: Hackathon Judges

**Key Message**: The Smart Financial Advisor effectively processes financial transaction data to provide quick, relevant insights and automate analytical tasks.

--- 

**I. Introduction (0:00 - 0:15)**

*   **Visual**: Title card: "Smart Financial Advisor - AI Innovators Hackathon 2025"
*   **Voiceover**: "Welcome to the demo of the Smart Financial Advisor, built for the AI Innovators Hackathon 2025. This agent analyzes retail transaction data to provide actionable insights."
*   **Visual**: Briefly show the project structure (folders for code, data, docs).

**II. Data Ingestion & Preparation (0:15 - 0:45)**

*   **Voiceover**: "First, let's see how the system ingests and prepares data. We start with a raw CSV of transactions."
*   **Visual**: Show a snippet of the raw `jordan_transactions.csv`.
*   **Voiceover**: "Our Python scripts clean this data, handle inconsistencies, and normalize formats."
*   **Visual**: Briefly show the `data_ingestion_p1.py` script running (simulated or actual console output showing success messages).
*   **Voiceover**: "The cleaned data is then stored in an SQL database for structured queries and vectorized into a FAISS index for semantic search."
*   **Visual**: Show `data_ingestion_p2.py` running (console output showing SQL storage and FAISS index creation success). Briefly show the SQLite DB structure (e.g., table schema) and mention the FAISS index file.

**III. Conversational Querying & Semantic Search (0:45 - 1:30)**

*   **Voiceover**: "Now, let's ask the advisor a question in natural language. We'll use our RAG agent script for this."
*   **Visual**: Show the `rag_agent_p1.py` script. Highlight the sample query: `"failed sales at Z Mall Al Bayader recently"`.
*   **Voiceover**: "The agent uses semantic search to find relevant transactions in the FAISS index and then retrieves detailed information from the SQL database."
*   **Visual**: Show the script executing and the console output displaying:
    *   The semantic search results (transaction IDs and scores).
    *   The detailed transaction information retrieved from SQL for those IDs.
*   **Voiceover**: "As you can see, it accurately retrieves relevant failed transactions for the specified mall. This demonstrates its ability to understand context and combine data sources."
*   **(Optional - if time permits for a second quick query)**
    *   **Voiceover**: "Let's try another query, like 'refunds at C Mall Amman'."
    *   **Visual**: Quickly show the query changed in the script, run, and show results.

**IV. Autonomous Workflows: Anomaly Detection (1:30 - 2:15)**

*   **Voiceover**: "The advisor also supports autonomous workflows, such as anomaly detection."
*   **Visual**: Show the `workflow_anomaly_detection.py` script.
*   **Voiceover**: "This script can identify unusual patterns, like a sudden spike in failed transactions or transactions with unusually high or low amounts."
*   **Visual**: Show the script executing and the console output displaying:
    *   The check for high failed transaction rates (e.g., "No recent transactions found for Z Mall..." or an actual alert if data is seeded for it).
    *   The detection of transactions with unusual amounts, listing some examples.
    *   The simulated alert messages.
*   **Voiceover**: "These workflows can be configured and, in a production environment, integrated with notification systems to alert managers to potential issues proactively."

**V. Conclusion & Key Deliverables (2:15 - 2:30)**

*   **Voiceover**: "In summary, the Smart Financial Advisor demonstrates a robust pipeline for data analysis, natural language querying, and automated insights. Key deliverables include the Python scripts for each component, the processed databases, and comprehensive documentation."
*   **Visual**: Show the `README.md` file briefly. Show a slide with key deliverables listed (Working application scripts, Automated workflow configuration, GitHub repository with documentation).
*   **Voiceover**: "Thank you for watching!"
*   **Visual**: End card with project name and team/participant name.

--- 

**Technical Notes for Demo Preparation:**

*   Ensure all scripts run smoothly and paths are correct for the demo environment.
*   Prepare console outputs to be clear and illustrative. May need to slightly modify print statements for demo clarity if actual output is too verbose.
*   For the "high failed transaction rate" anomaly, the current dataset might not trigger it with a short time window. The demo script uses a 7-day window to likely get *some* data; for the demo, either adjust this or mention it's looking at a broader historical period to find an example if live data doesn't show it.
*   Keep transitions quick and focus on the outputs that demonstrate functionality.
