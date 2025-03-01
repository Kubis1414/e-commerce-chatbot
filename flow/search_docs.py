from promptflow import tool
import os
import json
import sys
import numpy as np
from typing import List, Dict

# Přidání cesty k utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils.db_manager import VectorDBManager

@tool
def search_docs(search_query: str) -> List[Dict]:
    """
    Searches for relevant documents in the vector database.
    """
    # Inicializace správce vektorové databáze
    db_manager = VectorDBManager()
    
    # Vyhledání relevantních dokumentů (vrací top 50)
    retrieved_docs = db_manager.search(search_query, top_k=50)
    
    return retrieved_docs
