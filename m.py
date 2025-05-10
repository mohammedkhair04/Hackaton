from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (including your HTML)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the HTML file directly
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# API endpoint for query processing
@app.post("/api/query")
async def handle_query(query_text: str = Form(...)):
    # Process the query with your advisor logic
    # Replace this with actual processing from advisor_logic.py
    processed_result = f"Processed query: {query_text}"
    return JSONResponse({"results": processed_result})

# API endpoint for anomaly detection
@app.post("/api/run_anomaly_detection")
async def run_anomaly_detection():
    # Run your anomaly detection workflow
    # Replace this with actual processing from workflow_anomaly_detection.py
    anomaly_results = "Anomaly detection completed. Found 3 unusual patterns."
    return JSONResponse({"results": anomaly_results})