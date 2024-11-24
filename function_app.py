import azure.functions as func
import logging
import mlflow
from fastapi import FastAPI
from azure.storage.blob import BlobServiceClient
from fastapi.responses import JSONResponse
from azure.functions import AsgiMiddleware
import os

# Inicializar FastAPI
app = FastAPI()

# Função para baixar o modelo do Azure Blob Storage
def download_model_from_blob(container_name, model_name):
    """
    Baixa o modelo treinado armazenado no Azure Blob Storage e carrega com MLflow.
    """
    # Obter a connection string da variável de ambiente
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not connection_string:
        raise ValueError("A connection string do Azure Blob Storage não está definida.")

    # Conectar ao Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    # Baixar o modelo para um diretório temporário
    model_path = "/tmp/recommendation_model"
    blob_client = container_client.get_blob_client(model_name)
    
    with open(model_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())
    
    # Carregar o modelo usando MLflow
    model = mlflow.pyfunc.load_model(model_path)
    return model

# Adicionar as rotas do FastAPI
@app.get("/")
async def home():
    """
    Rota inicial para testar se a função está funcionando.
    """
    return {"message": "Azure Functions + FastAPI working!"}

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    """
    Rota que gera recomendações com base no user_id.
    """
    # Dados de conexão com o Azure Blob Storage
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")  # Variável de ambiente
    container_name = "datasets"  # Substitua com o nome do seu container no Blob Storage
    model_name = "models/recommendation_model"  # Substitua com o nome do modelo armazenado no Blob
    
    if not connection_string:
        raise ValueError("A connection string do Azure Blob Storage não está definida.")

    # Baixar o modelo do Azure Blob Storage
    model = download_model_from_blob(container_name, model_name)
    
    # Aqui, você precisa de um método para gerar recomendações com o modelo
    # Exemplo de recomendação simples (isso depende do seu modelo e como ele foi treinado)
    
    # Supondo que o modelo tenha um método `recommendForUserSubset`
    recommendations = model.recommendForUserSubset([[user_id]], 10)
    
    # Retorna a recomendação em formato JSON
    return JSONResponse(content={"user_id": user_id, "recommendations": recommendations.collect()})

# Integrando FastAPI com Azure Functions
function_app = func.FunctionApp()

@function_app.route(route="{*path}", auth_level=func.AuthLevel.ANONYMOUS)
async def fastapi_handler(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """
    Função que direciona todas as requisições para o FastAPI.
    """
    asgi_middleware = AsgiMiddleware(app)
    return await asgi_middleware.handle_async(req, context)
