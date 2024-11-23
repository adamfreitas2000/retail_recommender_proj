import azure.functions as func
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from azure.functions import AsgiMiddleware

# Initialize FastAPI
app = FastAPI()

# Add FastAPI routes
@app.get("/")
async def home():
    return {"message": "Azure Functions + FastAPI working!"}

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    recommendations = ["item1", "item2", "item3"]
    return {"user_id": user_id, "recommendations": recommendations}

# Integrate FastAPI with Azure Functions
function_app = func.FunctionApp()

@function_app.route(route="{*path}", auth_level=func.AuthLevel.ANONYMOUS)
async def fastapi_handler(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Route all requests to FastAPI."""
    asgi_middleware = AsgiMiddleware(app)
    return await asgi_middleware.handle_async(req, context)
