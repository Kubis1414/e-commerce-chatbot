from promptflow.core import tool
from typing import List
import time


@tool
def get_documents_from_vector_db(search_queries: List[str]) -> List[str]:
    documents = []
    
    for query in search_queries:
        # Simulate fetching documents from a vector database
        documents.append(f"Document for query: {query}")
        time.sleep(0.2)
        
    return documents
