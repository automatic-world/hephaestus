
from fastapi import FastAPI
from mangum import Mangum

# Create FastAPI application
app = FastAPI(
    title="Hephaestus API",
    description="FastAPI application with Mangum for AWS Lambda",
    version="1.0.0"
)

# Hello World endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, World!", "service": "Hephaestus"}

# Hello with name parameter
@app.get("/hello/{name}")
def read_hello(name: str):
    return {"message": f"Hello, {name}!", "service": "Hephaestus"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Hephaestus"}

# Items endpoint with query parameters (FastAPI sample)
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q, "service": "Hephaestus"}

# Create the Lambda handler using Mangum
handler = Mangum(app, lifespan="off")

# Keep the original lambda_handler for backward compatibility
def lambda_handler(event, context):
    """
    AWS Lambda handler function that uses Mangum to process FastAPI requests
    """
    return handler(event, context)