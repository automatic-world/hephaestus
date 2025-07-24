#!/usr/bin/env python3
"""
Local test script for the FastAPI application
Run this to test the FastAPI app locally before deploying to Lambda
"""

import uvicorn
from execute import app

if __name__ == "__main__":
    print("Starting FastAPI application locally...")
    print("Access the API documentation at: http://localhost:8000/docs")
    print("Access the API at: http://localhost:8000")
    print("\nAvailable endpoints:")
    print("  GET /          - Hello World")
    print("  GET /hello/{name} - Hello with name")
    print("  GET /health    - Health check")
    print("  GET /items/{item_id} - Items with query params")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 