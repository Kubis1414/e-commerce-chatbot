import weaviate
import weaviate.classes as wvc
import os
from typing import List, Optional


class WeaviateService:
    """
    Třída pro obsluhu spojení a dotazů do Weaviate databáze,
    konkrétně pro kolekci produktů.
    """

    def __init__(
        self,
        http_host: str = "130.61.26.171",
        http_port: int = 8080,
        grpc_host: str = "130.61.26.171",
        grpc_port: int = 50051,
        weaviate_api_key: str = os.getenv("WEAVIATE_API_KEY", ""),
        openai_api_key: str = os.getenv("OPENAI_API_KEY", ""),
        collection_name: str = "Apple_Products"
    ):
        """
        Inicializuje a připojí klienta k Weaviate.

        Args:
            http_host: Hostname nebo IP adresa pro HTTP spojení.
            http_port: Port pro HTTP spojení.
            grpc_host: Hostname nebo IP adresa pro gRPC spojení.
            grpc_port: Port pro gRPC spojení.
            weaviate_api_key: API klíč pro autentizaci k Weaviate.
            openai_api_key: API klíč pro OpenAI (potřebný pro vektorizaci dotazů).
                           Pokud není zadán, pokusí se načíst z env proměnné OPENAI_API_KEY.
            collection_name: Název kolekce ve Weaviate.
        """
        self.collection_name = collection_name
        self.client = None

        print("Pokouším se připojit k Weaviate...")
        auth_config = weaviate.auth.AuthApiKey(api_key=weaviate_api_key)

        try:
            self.client = weaviate.connect_to_custom(
                http_host=http_host,
                http_port=http_port,
                http_secure=False,
                grpc_host=grpc_host,
                grpc_port=grpc_port,
                grpc_secure=False,
                auth_credentials=auth_config,
                headers={
                    "X-OpenAI-Api-Key": openai_api_key or ""
                }
            )
            self.client.connect()

            if not self.client.is_ready():
                # Pokud se nepodaří připojit nebo není ready, vyvoláme chybu
                raise ConnectionError("Nepodařilo se připojit k Weaviate nebo instance není připravena.")

            print(f"Úspěšně připojeno k Weaviate. Stav: ready={self.client.is_ready()}")

            if not self.client.collections.exists(self.collection_name):
                print(f"Varování: Kolekce '{self.collection_name}' neexistuje v Weaviate!")
                raise ValueError(f"Kolekce '{self.collection_name}' neexistuje.")

        except Exception as e:
            print(f"Chyba při inicializaci WeaviateService: {e}")
            raise

    def search_products(
        self,
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        product_code: Optional[str] = None,
        limit: int = 5,
        return_props: Optional[List[str]] = None
    ) -> List[wvc.data.DataObject]:
        """
        Provádí vektorové vyhledávání (nearText) v kolekci produktů
        s možností filtrování podle ceny a produktového kódu.

        Args:
            query: Textový dotaz pro sémantické vyhledávání.
            min_price: Minimální cena produktu (včetně).
            max_price: Maximální cena produktu (včetně).
            product_code: Přesný produktový kód pro filtrování.
            limit: Maximální počet vrácených výsledků.
            return_props: Seznam názvů vlastností, které mají být vráceny.
                          Pokud None, vrátí se výchozí sada (např. název, cena, kód, url).

        Returns:
            Seznam nalezených objektů Weaviate (wvc.data.DataObject),
            každý obsahuje vlastnosti a metadata (včetně distance).
            Vrací prázdný seznam, pokud nic nenajde nebo nastane chyba.
        """
        
        if not self.client or not self.client.is_connected():
            print("Chyba: Klient Weaviate není připojen.")
            return []

        try:
            produkty_collection = self.client.collections.get(self.collection_name)

            # --- Sestavení filtrů ---
            filters_list = []
            if min_price is not None:
                filters_list.append(wvc.query.Filter.by_property("price").greater_than(min_price))
            if max_price is not None:
                filters_list.append(wvc.query.Filter.by_property("price").less_than(max_price))
            if product_code:
                # Předpokládáme, že 'product_code' je název property ve schématu
                filters_list.append(wvc.query.Filter.by_property("product_code").equal(product_code))

            # Kombinujeme filtry pomocí AND (musí platit všechny)
            combined_filter = None
            if len(filters_list) > 1:
                combined_filter = wvc.query.Filter.all_of(filters_list)
            elif len(filters_list) == 1:
                combined_filter = filters_list[0]
            # Pokud je filters_list prázdný, combined_filter zůstane None

            # --- Definice vrácených vlastností ---
            if return_props is None:
                # Výchozí sada vlastností k vrácení
                return_props = ["name", "price", "product_code", "url", "content"]

            # --- Provedení dotazu ---
            response = produkty_collection.query.near_text(
                query=query,
                limit=limit,
                filters=combined_filter, # Předáme sestavený filtr
                return_properties=return_props,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            return response.objects

        except Exception as e:
            print(f"Chyba při vyhledávání v Weaviate: {e}")
            return [] # V případě chyby vrátíme prázdný seznam

    def close(self):
        """Uzavře spojení s Weaviate, pokud existuje."""
        if self.client and self.client.is_connected():
            self.client.close()
            print("Spojení s Weaviate uzavřeno.")
        self.client = None # Resetujeme klienta

# --- Příklad použití (tento kód se spustí, jen když spustíš přímo tento soubor) ---
if __name__ == "__main__":
    print("Spouštím příklad použití WeaviateService...")

    weaviate_service = None # Inicializace pro finally blok
    try:
        # Vytvoření instance třídy - připojí se k Weaviate
        weaviate_service = WeaviateService()

        # --- Příklad 1: Obecný dotaz ---
        print("\n--- Příklad 1: Hledání 'rychlý MacBook' ---")
        results1 = weaviate_service.search_products(query="rychlý macbook", limit=3)
        if results1:
            for obj in results1:
                print(f"  Vzdálenost: {obj.metadata.distance:.4f}")
                print(f"  Název: {obj.properties.get('name')}")
                print(f"  Cena: {obj.properties.get('price')}")
                print("-" * 10)
        else:
            print("  Nenalezeno.")

        # --- Příklad 2: Dotaz s cenovým rozpětím ---
        print("\n--- Příklad 2: Hledání 'sluchátka přes hlavu' s cenou 5000-15000 Kč ---")
        results2 = weaviate_service.search_products(
            query="sluchátka přes hlavu",
            min_price=5000.0,
            max_price=15000.0,
            limit=3
        )
        if results2:
             for obj in results2:
                print(f"  Vzdálenost: {obj.metadata.distance:.4f}")
                print(f"  Název: {obj.properties.get('name')}")
                print(f"  Cena: {obj.properties.get('price')}")
                print("-" * 10)
        else:
            print("  Nenalezeno.")

        # --- Příklad 3: Dotaz s konkrétním kódem produktu (méně časté s nearText, ale možné) ---
        # Najdeme produkt podle kódu a pak můžeme použít jeho vektor pro nearVector hledání,
        # nebo jen pro ověření, že filtr funguje. Zde použijeme nearText s filtrem.
        target_code = "JA940i9d" # Kód z tvých ukázkových dat
        print(f"\n--- Příklad 3: Hledání 'bezdrátová sluchátka' s kódem '{target_code}' ---")
        results3 = weaviate_service.search_products(
            query="bezdrátová sluchátka", # Query může být obecnější, když filtrujeme na kód
            product_code=target_code,
            limit=1
        )
        if results3:
            obj = results3[0]
            print(f"  Vzdálenost: {obj.metadata.distance:.4f}")
            print(f"  Název: {obj.properties.get('name')}")
            print(f"  Kód: {obj.properties.get('product_code')}")
            print(f"  Cena: {obj.properties.get('price')}")
            print("-" * 10)
        else:
            print("  Nenalezeno.")

    except Exception as e:
        print(f"Nastala chyba v příkladu použití: {e}")

    finally:
        # Vždy se pokusíme uzavřít spojení, i když došlo k chybě
        if weaviate_service:
            weaviate_service.close()