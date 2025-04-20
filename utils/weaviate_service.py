import os
import weaviate
import weaviate.classes as wvc
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any
from .config import WEAVIATE_URL


class Document(BaseModel):
    """Represents a single product document retrieved from Weaviate."""
    name: Optional[str] = Field(default=None, description="Product name.")
    content: Optional[str] = Field(default=None, description="Vectorized content of the product.")
    url: Optional[str] = Field(default=None, description="Product URL.")
    product_code: Optional[str] = Field(default=None, description="Product code.")
    price: Optional[float] = Field(default=None, description="Product price.")


class SearchQuery(BaseModel):
    """
    Represents optional filters that can be applied to a search query.
    Used as a nested model within OutputSchema.
    """
    query: str = Field(
        ...,
        description="The core query string for semantic vector search. This text will be vectorized and compared against product content vectors."
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Optional inclusive minimum price filter. Only products with price >= min_price will be matched.",
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Optional inclusive maximum price filter. Only products with price <= max_price will be matched.",
    )
    product_code: Optional[str] = Field(
        default=None,
        description="Optional exact product code to filter by. Useful for finding a specific item variation."
    )

    @model_validator(mode='after')
    def check_prices(self) -> 'SearchQuery':
        """Validates that min_price is not greater than max_price if both are set."""
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot be greater than max_price")
        return self


class WeaviateService:
    """
    Třída pro obsluhu spojení a dotazů do Weaviate databáze,
    konkrétně pro kolekci produktů.
    """

    def __init__(
        self,
        http_host: str = WEAVIATE_URL,
        http_port: int = 8080,
        grpc_host: str = WEAVIATE_URL,
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
    
    def extract_and_print_properties(self, weaviate_results) -> List[Document]:
        """
        Vezme seznam výsledků z Weaviate (očekává strukturu [[{obj1}, {obj2}, ...]]),
        extrahuje slovník 'properties' z každého objektu a vypíše je formátovaně.

        Args:
            weaviate_results: Seznam obsahující seznam objektů vrácených z Weaviate.

        Returns:
            Seznam slovníků, kde každý slovník jsou 'properties' jednoho produktu.
            Vrací prázdný seznam, pokud vstup nemá očekávaný formát nebo nejsou nalezeny properties.
        """
        extracted_products = []

        if not isinstance(weaviate_results, list) or len(weaviate_results) == 0:
            print("Chyba: Vstupní data nemají očekávaný formát list.")
            return extracted_products

        for i, obj in enumerate(weaviate_results):
            props = obj.properties

            if isinstance(props, dict):
                doc = Document(**props) 
                extracted_products.append(doc)
            else:
                print(f"Varování: Objekt na indexu {i} nemá platný slovník 'properties'.")

        if not extracted_products:
            print("Nebyly nalezeny žádné vlastnosti ('properties') k zobrazení.")

        return extracted_products


    def search_products(
        self,
        search_params: dict[str, Any],
        limit: int = 5
        ) -> List[Document]:
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

        query = search_params.query
        if not query or not isinstance(query, str):
            print("Chyba: Parametr 'query' chybí nebo není řetězec v search_params.")
            return []
        
        min_price = search_params.min_price
        max_price = search_params.max_price
        product_code = search_params.product_code
        
        if min_price is not None and not isinstance(min_price, (int, float)):
            print(f"Varování: 'min_price' není číslo ({type(min_price)}), bude ignorováno.")
            min_price = None
        if max_price is not None and not isinstance(max_price, (int, float)):
            print(f"Varování: 'max_price' není číslo ({type(max_price)}), bude ignorováno.")
            max_price = None
        if product_code is not None and not isinstance(product_code, str):
            print(f"Varování: 'product_code' není řetězec ({type(product_code)}), bude ignorováno.")
            product_code = None
        if not isinstance(limit, int) or limit <= 0:
            print(f"Varování: 'limit' není kladné celé číslo ({limit}), použije se výchozí 5.")
            limit = 5
    
        try:
            apple_collection = self.client.collections.get(self.collection_name)

            # Sestavení filtrů
            filters_list = []
            if min_price is not None:
                filters_list.append(wvc.query.Filter.by_property("price").greater_than(min_price))
            if max_price is not None:
                filters_list.append(wvc.query.Filter.by_property("price").less_than(max_price))
            if product_code:
                filters_list.append(wvc.query.Filter.by_property("product_code").equal(product_code))

            # Kombinujeme filtry pomocí AND
            combined_filter = None
            if len(filters_list) > 1:
                combined_filter = wvc.query.Filter.all_of(filters_list)
            elif len(filters_list) == 1:
                combined_filter = filters_list[0]
            # Pokud je filters_list prázdný, combined_filter zůstane None

            # Definice vlastností, které se mají vrátit z weaviate
            return_props = ["name", "price", "product_code", "url", "content"]

            # Provedení dotazu 
            response = apple_collection.query.near_text(
                query=query,
                limit=limit,
                filters=combined_filter,
                return_properties=return_props,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )
            
            output = self.extract_and_print_properties(response.objects)     
              
            return output

        except Exception as e:
            print(f"Chyba při vyhledávání v Weaviate: {e}")
            return []

    def close(self):
        """Uzavře spojení s Weaviate, pokud existuje."""
        if self.client and self.client.is_connected():
            self.client.close()
            print("Spojení s Weaviate uzavřeno.")
        self.client = None # Resetujeme klienta
