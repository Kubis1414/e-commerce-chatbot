from promptflow.core import tool
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts.prompt import PromptTemplate
from utils.models import Models
from utils.weaviate_service import SearchQuery


class OutputSchema(BaseModel):
    """Output schema for the LLM that generates search queries."""

    search_queries: List[SearchQuery] = Field(default_factory=list, description="List of search queries that will be used to search the vector database for documents, related to the customer inquiry.")


@tool
def generate_search_queries(customer_input: str, chat_history: list, context: dict, llm_provider: str) -> List[SearchQuery]:    
    llm = Models.get_model(llm_provider, "mini")
    if not llm:
        raise ValueError(f"Nepodporovaný poskytovatel LLM: {llm_provider}")
    
    prompt = PromptTemplate.from_template('''
        Create a prompt that generates a list of search queries based on customer inquiries. 
        Use the chat history and context to ensure all technical details and product names are retained. 
        The output should be in Czech and formatted as a JSON object containing only the search queries list.
        These search queries should be suitable for use as lookup queries in a vector database.
        You can also set hard filters for prices which should be used, when a customer mentions price.
        Leave product code empty.
        
        Instructions:
            Interpret the customer inquiry to determine the products or components for which complete information is needed.
            Ensure all search queries are written in Czech.
            Respond in the following JSON format:
                "search_queries": [
                    "query": "",
                    "price_min": "",
                    "price_max": "",
                    "product_code": ""
                ]

        Context:
            The customer is currently on a page titled """{page_title}""" with URL """{current_url}""".
            
            Customer inquiry: """{customer_input}"""
            Chat history (first message in order is the newest one, last message in order is the oldest one): """{chat_history}"""
    ''')
    
    data = {
        "page_title": context.get("page_title", ""),
        "current_url": context.get("current_url", ""),
        "customer_input": customer_input,
        "chat_history": chat_history
    }
    
    structured_llm = llm.with_structured_output(OutputSchema, include_raw=True)
    chain = prompt | structured_llm
    
    output_data = chain.invoke(data)
    
    return output_data["parsed"].search_queries
