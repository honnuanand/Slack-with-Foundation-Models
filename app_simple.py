#!/usr/bin/env python3
"""Simple test app for Databricks Apps"""

import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Databricks Slack Bot",
    description="Test deployment",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "running",
        "message": "Databricks Slack Bot is operational",
        "environment": {
            "DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST", "not set"),
            "DATABRICKS_SECRET_SCOPE": os.environ.get("DATABRICKS_SECRET_SCOPE", "not set"),
            "PORT": os.environ.get("PORT", "8000")
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)