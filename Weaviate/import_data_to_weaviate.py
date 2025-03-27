import weaviate
import weaviate.classes as wvc
import csv, os, time, ast
from ..utils.config import WEAVIATE_URL 


# --- Konfigurace ---
csv_filename = "apple_data.csv"
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
print(f"API_KEY: {WEAVIATE_API_KEY}")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COLLECTION_NAME = "Apple_Products"
BATCH_SIZE = 100

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

    # --- Definice a vytvoření schématu (kolekce) ---
    print(f"Kontrola/vytváření kolekce '{COLLECTION_NAME}'...")

    if not client.collections.exists(COLLECTION_NAME):
        client.collections.create(
            name=COLLECTION_NAME,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),
            properties=[
                wvc.config.Property(
                    name="name",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    tokenization=wvc.config.Tokenization.WORD # Povolí fulltext
                ),
                # Content - TOTO POLE VEKTORIZUJEME
                wvc.config.Property(
                    name="content",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=False,
                    tokenization=wvc.config.Tokenization.WORD # Pro případné hybridní hledání
                ),
                wvc.config.Property(
                    name="url",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    tokenization=wvc.config.Tokenization.FIELD
                ),
                wvc.config.Property(
                    name="prefix",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    tokenization=wvc.config.Tokenization.FIELD
                ),
                wvc.config.Property(
                    name="manufacturer",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    tokenization=wvc.config.Tokenization.FIELD
                ),
                # productCode uložíme jako text (může obsahovat formát jako ['code'])
                wvc.config.Property(
                    name="product_code",
                    data_type=wvc.config.DataType.TEXT,
                    skip_vectorization=True,
                    tokenization=wvc.config.Tokenization.FIELD
                ),
                wvc.config.Property(
                    name="price",
                    data_type=wvc.config.DataType.NUMBER,
                    skip_vectorization=True,
                ),
                wvc.config.Property(
                    name="is_main_product",
                    data_type=wvc.config.DataType.INT, # INT pro 0 nebo 1
                    skip_vectorization=True,
                ),
                wvc.config.Property(
                    name="is_accessory",
                    data_type=wvc.config.DataType.INT, # INT pro 0 nebo 1
                    skip_vectorization=True,
                ),
            ]
        )
        print(f"Kolekce '{COLLECTION_NAME}' vytvořena.")
    else:
        print(f"Kolekce '{COLLECTION_NAME}' již existuje.")

    # --- Získání reference ke kolekci ---
    apple_collection = client.collections.get(COLLECTION_NAME)

    # --- Čtení CSV a import dat v dávkách ---
    print(f"Zahajuji import dat z {CSV_FILE_PATH}...")
    objects_to_insert = []
    skipped_rows = 0
    imported_count = 0
    start_time = time.time()

    try:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter='|')

            # Ověření existence základních sloupců (volitelné, ale užitečné)
            required_cols = ['uuid', 'name', 'content', 'priceFrom', 'mainProductInd', 'accessoryInd']
            if not all(col in reader.fieldnames for col in required_cols):
                print(f"Varování: CSV souboru ({csv_filename}) mohou chybět některé očekávané sloupce.")
                print(f"Očekávané (alespoň): {required_cols}")
                print(f"Nalezené: {reader.fieldnames}")

            row_num = 1
            for row in reader:
                row_num += 1
                try:
                    if not row.get('uuid') or not row.get('content'):
                        print(f"Varování: Přeskakuji řádek {row_num} - chybí 'uuid' nebo 'content'.")
                        skipped_rows += 1
                        continue

                    # Sestavení objektu pro Weaviate (klíče = názvy properties ve schématu)
                    properties = {
                        "uuid": row['uuid'],
                        "name": row.get('name'),
                        "content": row['content'], # Tento text bude vektorizován
                        "url": row.get('url'),
                        "prefix": row.get('prefix'),
                        "manufacturer": row.get('manufacturer'),
                    }

                    # --- Zpracování productCode ---
                    product_code_str = row.get('productCode')
                    cleaned_product_code = None # Výchozí hodnota, pokud se nepodaří extrahovat
                    if product_code_str:
                        try:
                            # Pokusíme se vyhodnotit string jako Python list
                            evaluated_list = ast.literal_eval(product_code_str)
                            # Pokud je to list a má alespoň jeden prvek...
                            if isinstance(evaluated_list, list) and len(evaluated_list) > 0:
                                # ...vezmeme první prvek
                                cleaned_product_code = evaluated_list[0]
                                # Volitelně: Ověřit, že je to string, pro jistotu
                                if not isinstance(cleaned_product_code, str):
                                    cleaned_product_code = str(cleaned_product_code)
                            elif isinstance(evaluated_list, str):
                                # Pokud to náhodou byl už jen string (bez listu), použijeme ho
                                cleaned_product_code = evaluated_list
                            else:
                                print(f"Varování: 'productCode' ('{product_code_str}') na řádku {row_num} není očekávaný list nebo string. Používám None.")
                        except (ValueError, SyntaxError):
                            # Pokud se string nepodařilo vyhodnotit (není to platný Python literál)
                            # Může to být už čistý kód, nebo něco jiného. Zkusíme základní očištění.
                            print(f"Varování: 'productCode' ('{product_code_str}') na řádku {row_num} nemá formát seznamu. Používám hodnotu po očištění.")
                            cleaned_product_code = product_code_str.strip("[]'\" ") # Odstraní běžné znaky okolo
                        except Exception as e:
                            # Jiná neočekávaná chyba
                            print(f"Chyba při zpracování 'productCode' ('{product_code_str}') na řádku {row_num}: {e}. Používám None.")

                    properties["product_code"] = cleaned_product_code # Uložíme očištěný kód (nebo None)

                    # Převod číselných hodnot s ošetřením chyb
                    try:
                        properties["price"] = float(row['priceFrom']) if row.get('priceFrom') else None
                    except (ValueError, TypeError):
                        print(f"Varování: Neplatná hodnota 'priceFrom' ('{row.get('priceFrom')}') na řádku {row_num} (UUID: {row['uuid']}). Nastavuji None.")
                        properties["price"] = None

                    try:
                        properties["is_main_product"] = int(row['mainProductInd']) if row.get('mainProductInd') is not None else 0
                    except (ValueError, TypeError):
                        print(f"Varování: Neplatná hodnota 'mainProductInd' ('{row.get('mainProductInd')}') na řádku {row_num} (UUID: {row['uuid']}). Nastavuji 1.")
                        properties["is_main_product"] = 1

                    try:
                        properties["is_accessory"] = int(row['accessoryInd']) if row.get('accessoryInd') is not None else 0
                    except (ValueError, TypeError):
                        print(f"Varování: Neplatná hodnota 'accessoryInd' ('{row.get('accessoryInd')}') na řádku {row_num} (UUID: {row['uuid']}). Nastavuji 0.")
                        properties["is_accessory"] = 0

                    objects_to_insert.append(wvc.data.DataObject(properties=properties))

                    # Pokud dosáhneme velikosti dávky, vložíme data
                    if len(objects_to_insert) >= BATCH_SIZE:
                        current_batch_size = len(objects_to_insert)
                        imported_count += current_batch_size
                        print(f"Vkládám dávku {current_batch_size} objektů (celkem {imported_count})...")
                        result = apple_collection.data.insert_many(objects_to_insert)

                        if result.has_errors:
                            print(f"Chyby při vkládání dávky:")

                            for i, err_obj in result.errors.items():
                                print(f"  - Objekt index {i}: {err_obj.message}")
                                print(f"    Data: {objects_to_insert[i].properties}")

                        objects_to_insert = []

                except Exception as e:
                    print(f"Neočekávaná chyba při zpracování řádku {row_num} (UUID: {row.get('uuid', 'N/A')}): {e}. Přeskakuji.")
                    skipped_rows += 1
                    print(f"Data řádku: {row}")

            if objects_to_insert:
                final_batch_size = len(objects_to_insert)
                imported_count += final_batch_size
                print(f"Vkládám poslední dávku {final_batch_size} objektů (celkem {imported_count})...")
                result = apple_collection.data.insert_many(objects_to_insert)
                if result.has_errors:
                     print(f"Chyby při vkládání poslední dávky:")
                     for i, err_obj in result.errors.items():
                         print(f"  - Objekt index {i}: {err_obj.message}")

        end_time = time.time()
        print(f"\nImport dokončen.")
        print(f"Celkem úspěšně zpracováno pro import: {imported_count}")
        print(f"Přeskočeno řádků kvůli chybám/neúplnosti: {skipped_rows}")
        print(f"Celkový čas: {end_time - start_time:.2f} sekund.")

    except FileNotFoundError:
        print(f"Chyba: CSV soubor nebyl nalezen na cestě: {CSV_FILE_PATH}")
    except Exception as e:
        print(f"Chyba při čtení nebo zpracování CSV: {e}")


except Exception as e:
    print(f"Chyba při připojování nebo operaci s Weaviate: {e}")

finally:
    if 'client' in locals() and client.is_connected():
        client.close()
        print("Spojení s Weaviate uzavřeno.")
