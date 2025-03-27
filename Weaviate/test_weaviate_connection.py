import weaviate
import os
from weaviate.classes.init import AdditionalConfig, Timeout
from ..utils.config import WEAVIATE_URL 

auth_config = weaviate.auth.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY", ""))

client = weaviate.connect_to_custom(
    http_host=WEAVIATE_URL,
    http_port=8080,
    http_secure=False,
    grpc_host=WEAVIATE_URL,
    grpc_port=50051,
    grpc_secure=False,
    auth_credentials=auth_config,
    additional_config=AdditionalConfig(
        timeout=Timeout(init=30, query=120, insert=180)
    ),
    headers={
        "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY", ""),
        'User-Agent': 'python-user'}
)

print("Připojování...")
client.connect()

print(f"Stav připojení: {client.is_connected()}")
print(f"Stav připravenosti: {client.is_ready()}")

client.close()
