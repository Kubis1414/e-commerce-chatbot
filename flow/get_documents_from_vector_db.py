from promptflow.core import tool
from typing import List

from utils.weaviate_service import WeaviateService, SearchQuery

@tool
def get_documents_from_vector_db(search_queries: List[SearchQuery]) -> List:
    documents = []
    service = WeaviateService()
    
    for query in search_queries:
        retrieved_documents = service.search_products(search_params=query, limit=5)
        documents.append(retrieved_documents)
    
    service.close()
    
    return documents
