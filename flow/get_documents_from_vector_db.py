from promptflow.core import tool
from typing import List

from utils.weaviate_service import WeaviateService, SearchQuery

@tool
def get_documents_from_vector_db(search_queries: List[SearchQuery]) -> List:
    documents = []
    service = WeaviateService()
    
    for query in search_queries:
        retrieved_documents = service.search_products(search_params=query, limit=5)
        for doc in retrieved_documents:
            documents.append(doc)
    
    service.close()
    
    #deduplikace dokumentu
    output_documents: list = []
    seen_documents = set()
    
    for item in documents:
        if item.content not in seen_documents:
            output_documents.append(item)
            seen_documents.add(item.content)
    
    return output_documents
