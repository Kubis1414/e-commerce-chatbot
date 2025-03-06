from promptflow.core import tool
from typing import Optional, List, Dict
from pydantic import BaseModel
import json, os, time


class Customer(BaseModel):
    customer_id: Optional[str] = None
    name: Optional[str] = None
    vokative: Optional[str] = None
    email: Optional[str] = None
    favorite_brands: Optional[List[str]] = None


def get_customer_data_from_api(customer_id: str) -> Dict:
    """
    Simuluje volání API načtením dat ze sample souboru.
    V reálném případě by zde bylo volání skutečného API.
    """
    
    try:
        # Načtení sample dat ze souboru
        sample_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data", "customers.json")
        with open(sample_data_path, "r", encoding="utf-8") as f:
            customers_data = json.load(f)
        
        time.sleep(0.3)
        # Najdeme zákazníka v seznamu podle customer_id
        for customer in customers_data:
            if customer.get("customer_id") == customer_id:
                return customer
        
        # Pokud zákazník neexistuje, vrátíme prázdný slovník
        return {}
    except Exception as e:
        print(f"Chyba při načítání dat zákazníka: {e}")
        return {}


@tool
def get_customer_info(customer_dict: dict) -> dict:
    """
    Zpracuje informace o zákazníkovi a případně doplní chybějící údaje z API.
    """
    
    # Pokud je dictionary prázdný, vrátíme prázdný Customer objekt
    if not customer_dict:
        return Customer().model_dump()
    
    # Vytvoříme Customer objekt z dictionary
    customer = Customer(**customer_dict)
    
    # Pokud máme jen customer_id a ostatní pole jsou prázdná, načteme data z API
    if customer.customer_id and all(
        not value for key, value in customer_dict.items() 
        if key != "customer_id"
    ):
        customer_data = get_customer_data_from_api(customer.customer_id)
        customer = Customer(**customer_data)
        return customer.model_dump()
    
    return customer.model_dump()
