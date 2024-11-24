import azure.functions as func
import logging
import os
import mlflow
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

def download_model_from_blob(container_name, model_name):
    """
    Baixa o modelo do Azure Blob Storage e carrega com MLflow.
    """
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING não foi definida nas variáveis de ambiente.")

    # Conectar ao Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    # Caminho temporário para salvar o modelo
    model_path = "/tmp/recommendation_model"
    blob_client = container_client.get_blob_client(model_name)
    
    with open(model_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())
    
    # Carregar o modelo com MLflow
    model = mlflow.pyfunc.load_model(model_path)
    return model

@app.route(route="recommendations", auth_level=func.AuthLevel.ANONYMOUS)
def recommendations(req: func.HttpRequest) -> func.HttpResponse:
    """
    Processa a requisição HTTP e retorna recomendações.
    """
    logging.info('Requisição recebida para /recommendations')

    # Exemplo fictício de ID do usuário
    user_id = req.params.get('user_id')
    if not user_id:
        return func.HttpResponse(
            "Por favor, passe o parâmetro 'user_id' na query string.",
            status_code=400
        )

    # Conectar ao Blob Storage e carregar o modelo
    try:
        container_name = "datasets"  # Substitua pelo seu container
        model_name = "models/recommendation_model"  # Substitua pelo nome do modelo no Blob Storage
        model = download_model_from_blob(container_name, model_name)
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo: {e}")
        return func.HttpResponse("Erro ao carregar o modelo.", status_code=500)

    # Gerar recomendações com base no user_id
    try:
        recommendations = model.recommendForUserSubset([[int(user_id)]], 10)
        return func.HttpResponse(
            f"Recomendações para o usuário {user_id}: {recommendations.collect()}",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Erro ao gerar recomendações: {e}")
        return func.HttpResponse("Erro ao gerar recomendações.", status_code=500)
