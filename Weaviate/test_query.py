import weaviate
import weaviate.classes as wvc
import os, json
from ..utils.config import WEAVIATE_URL 


# --- Konfigurace ---
csv_filename = "apple_data.csv"
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
print(f"API_KEY: {WEAVIATE_API_KEY}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COLLECTION_NAME = "Apple_Products"
BATCH_SIZE = 100

# search_query = "sluchátka s ANC"
# search_query = "notebook pro práci na cestách do 40 000"
# search_query = "nejlevnější iPhone"
search_query = "kryt na telefon ihpone 16 PRo max s MagSafe"

print(f"Hledám produkty podobné: '{search_query}'")

# --- Připojení k Weaviate ---
print("Připojování k Weaviate...")
auth_config = weaviate.auth.AuthApiKey(api_key=WEAVIATE_API_KEY)

try:
    client = weaviate.connect_to_custom(
        http_host=WEAVIATE_URL,
        http_port=8080,
        http_secure=False,
        grpc_host=WEAVIATE_URL,
        grpc_port=50051,
        grpc_secure=False,
        auth_credentials=auth_config,
        headers={
             "X-OpenAI-Api-Key": OPENAI_API_KEY
        }
    )
    client.connect()

    print(f"Připojeno: {client.is_connected()}, Připraveno: {client.is_ready()}")
    if not client.is_ready():
        raise ConnectionError("Weaviate není připraveno. Zkontrolujte logy serveru.")    
    
    # --- Získání reference ke kolekci ---
    produkty_collection = client.collections.get(COLLECTION_NAME)

    # --- Vektorové vyhledávání (nearText) ---
    response = produkty_collection.query.near_text(
        query=search_query,
        limit=5,
        return_properties=[
            "name",
            "content",
            "url",
            "price",
            "product_code"
        ],
        return_metadata=wvc.query.MetadataQuery(distance=True)
    )

    print("\nVýsledky vektorového vyhledávání:")
    if not response.objects:
        print("Nebyly nalezeny žádné relevantní produkty.")
    else:
        for obj in response.objects:
            print("-" * 30)
            print(f"Shoda (vzdálenost): {obj.metadata.distance:.4f}") # Nižší číslo = lepší shoda
            print(f"UUID: {obj.uuid}")
            print(json.dumps(obj.properties, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"Chyba při připojování nebo operaci s Weaviate: {e}")

finally:
    if 'client' in locals() and client.is_connected():
        client.close()
        print("Spojení s Weaviate uzavřeno.")
