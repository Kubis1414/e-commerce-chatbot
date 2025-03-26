import pytest
import os
import time

# Importujeme třídu, kterou chceme testovat
from utils.weaviate_service import WeaviateService


# Načtení údajů z environmentálních proměnných
WEAVIATE_API_KEY = os.getenv("WEAVIATE_TEST_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_TEST_API_KEY")
WEAVIATE_HTTP_HOST = os.getenv("WEAVIATE_TEST_HTTP_HOST", "130.61.26.171")
WEAVIATE_HTTP_PORT = int(os.getenv("WEAVIATE_TEST_HTTP_PORT", 8080))
WEAVIATE_GRPC_HOST = os.getenv("WEAVIATE_TEST_GRPC_HOST", "130.61.26.171")
WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_TEST_GRPC_PORT", 50051))
COLLECTION_NAME = "AppleProdukty" # Použijeme existující kolekci


# Důvod pro přeskočení, pokud chybí klíče
skip_reason = "Chybí env proměnné WEAVIATE_TEST_API_KEY nebo OPENAI_TEST_API_KEY pro integrační testy"

# Označení pro všechny testy v tomto souboru + podmíněné přeskočení
pytestmark = [
    pytest.mark.integration, # Označení jako integrační test
    pytest.mark.skipif(not WEAVIATE_API_KEY or not OPENAI_API_KEY, reason=skip_reason)
]


@pytest.fixture(scope="module") # scope="module" vytvoří instanci jen jednou pro celý soubor
def live_weaviate_service():
    """Fixture pro vytvoření instance WeaviateService proti živé DB."""
    print("\n[Fixture] Vytvářím instanci WeaviateService pro integrační testy...")
    service = None
    try:
        service = WeaviateService(
            http_host=WEAVIATE_HTTP_HOST,
            http_port=WEAVIATE_HTTP_PORT,
            grpc_host=WEAVIATE_GRPC_HOST,
            grpc_port=WEAVIATE_GRPC_PORT,
            weaviate_api_key=WEAVIATE_API_KEY,
            openai_api_key=OPENAI_API_KEY,
            collection_name=COLLECTION_NAME
        )
        # Krátká pauza po připojení pro jistotu
        time.sleep(2)
        yield service # Poskytne instanci testům

    except ConnectionError as e:
        pytest.fail(f"Nepodařilo se připojit k živé Weaviate DB pro testy: {e}")
    except Exception as e:
        pytest.fail(f"Neočekávaná chyba při inicializaci live_weaviate_service: {e}")

    finally:
        if service:
            print("\n[Fixture] Uzavírám spojení WeaviateService po testech.")
            service.close()

# --- Integrační Testy ---

def test_connection_and_readiness(live_weaviate_service):
    """Ověří, že poskytnutá instance služby je připojena a připravena."""
    assert live_weaviate_service.client is not None
    assert live_weaviate_service.client.is_connected() is True
    # is_ready() může někdy chvíli trvat, i když konstruktor prošel
    assert live_weaviate_service.client.is_ready() is True
    print("\n[Test] Spojení a připravenost ověřena.")

def test_search_basic_query(live_weaviate_service):
    """Testuje základní vektorové vyhledávání."""
    query = "MacBook" # Předpokládáme, že nějaký MacBook v datech je
    print(f"\n[Test] Hledám: '{query}'")
    results = live_weaviate_service.search_products(query=query, limit=3)

    # Základní ověření
    assert isinstance(results, list) # Musí vrátit seznam
    print(f"Nalezeno výsledků: {len(results)}")

    if results:
        print("První výsledek:")
        first_result = results[0]
        assert hasattr(first_result, 'properties')
        assert hasattr(first_result, 'metadata')
        assert hasattr(first_result.metadata, 'distance')
        print(f"  Name: {first_result.properties.get('name', 'N/A')}")
        print(f"  Distance: {first_result.metadata.distance:.4f}")
        # Ověříme, že vrácené properties obsahují alespoň 'name' (z výchozích)
        assert 'name' in first_result.properties
    else:
        # Pokud nic nenajde, test neselže, ale vypíšeme varování
        print("Varování: Základní dotaz na MacBook nevrátil žádné výsledky.")

def test_search_with_price_filter(live_weaviate_service):
    """Testuje vyhledávání s cenovým filtrem."""
    # Zvolte cenové rozpětí, kde pravděpodobně něco bude
    query = "sluchátka"
    min_p = 1000.0
    max_p = 10000.0
    print(f"\n[Test] Hledám: '{query}' s cenou {min_p}-{max_p} Kč")
    results = live_weaviate_service.search_products(
        query=query,
        min_price=min_p,
        max_price=max_p,
        limit=5
    )

    assert isinstance(results, list)
    print(f"Nalezeno výsledků: {len(results)}")

    # Ověření filtru: Všechny výsledky musí splňovat cenové podmínky
    for obj in results:
        assert hasattr(obj, 'properties')
        price = obj.properties.get('price_from')
        assert price is not None, f"Objekt {obj.uuid} nemá cenu!"
        assert isinstance(price, (int, float))
        assert min_p <= price <= max_p, f"Objekt {obj.uuid} (cena {price}) nesplňuje filtr {min_p}-{max_p}!"
        print(f"  OK: {obj.properties.get('name', 'N/A')} (cena {price})")

    if not results:
        print(f"Varování: Dotaz na '{query}' s filtrem {min_p}-{max_p} nevrátil žádné výsledky.")


def test_search_with_product_code_filter(live_weaviate_service):
    """Testuje vyhledávání s filtrem na konkrétní produktový kód."""
    # Použijte kód, o kterém víte, že v DB existuje (nebo ho tam přidejte)
    # Pokud nevíte, tento test může selhat nebo nic nenajít.
    target_code = "JA940i9d" # Kód z předchozích příkladů
    if not target_code:
        pytest.skip("Není definován cílový produktový kód pro test.")

    query = "sluchátka" # Dotaz může být obecný, spoléháme na filtr
    print(f"\n[Test] Hledám: '{query}' s kódem '{target_code}'")
    results = live_weaviate_service.search_products(
        query=query,
        product_code=target_code,
        limit=1 # Očekáváme max 1 výsledek s unikátním kódem
    )

    assert isinstance(results, list)
    print(f"Nalezeno výsledků: {len(results)}")

    if target_code: # Pokud byl kód zadán pro test
      if not results:
          print(f"Varování: Nebyl nalezen produkt s kódem '{target_code}'.")
          # Můžeme zde test označit za selhaný, pokud očekáváme existenci kódu:
          # pytest.fail(f"Očekávaný produkt s kódem '{target_code}' nebyl nalezen.")
      else:
          assert len(results) == 1, "Nalezeno více produktů se stejným kódem?"
          obj = results[0]
          assert hasattr(obj, 'properties')
          assert obj.properties.get('product_code') == target_code
          print(f"  OK: Nalezen produkt '{obj.properties.get('name', 'N/A')}' s kódem {target_code}")
