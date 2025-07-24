
<p align="center">
<img width="120" height="120" alt="ChatGPT Image 2025년 7월 17일 오후 09_05_43" src="https://github.com/user-attachments/assets/aa746fd0-f982-45c5-b7b4-04fa1d04632c" />
</p>

<h1 align="center">
  <a href="">
     Forging innovation with the fire of Hephaestus
  </a>
</h1>

<p align="center">

  <strong>Hephaestus</strong><br>
</p>

<p align="center">
  <a href="https://github.com/lines-code/lines-assitant-things/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="React Native is released under the MIT license." />
  </a>
  
</p>

## FastAPI Integration with Mangum

This project now includes a FastAPI application integrated with Mangum for AWS Lambda deployment.

### Features

- **FastAPI Application**: Modern, fast web framework for building APIs with Python
- **Mangum Integration**: ASGI adapter for running FastAPI in AWS Lambda
- **Hello World Endpoints**: Sample endpoints demonstrating FastAPI functionality
- **Automatic API Documentation**: Interactive docs available at `/docs`

### Available Endpoints

- `GET /` - Hello World message
- `GET /hello/{name}` - Personalized greeting
- `GET /health` - Health check endpoint
- `GET /items/{item_id}` - Sample endpoint with path and query parameters

### Local Development

Run the FastAPI application locally:

```bash
# Using the test script
make fastapi_local

# Or directly with uvicorn
make fastapi_dev

# Or manually
uvicorn execute:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Deployment

The application is configured for AWS Lambda deployment using Mangum:

```bash
# Export dependencies
make poetry_export

# Install dependencies for Lambda
make python_install

# Create deployment package
make zip_deployment
```
