import re
from promptflow.core import tool
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts.prompt import PromptTemplate
from utils.models import Models, get_model_name, _extract_token_counts, TokenManager
from utils.weaviate_service import SearchQuery

    
class OutputSchema(BaseModel):
    """Output schema for the LLM that generates search queries."""

    search_queries: List[SearchQuery] = Field(default_factory=list, description="List of search queries that will be used to search the vector database for documents, related to the customer inquiry.")


class Output():
    def __init__(self, search_queries: OutputSchema, token_manager: TokenManager) -> None:
        self.search_queries = search_queries
        self.token_manager = token_manager


@tool
def generate_search_queries(customer_input: str, chat_history: list, context: dict, llm_provider: str) -> List[SearchQuery]:
    llm = Models.get_model(llm_provider, "mini")
    if not llm:
        raise ValueError(f"Nepodporovaný poskytovatel LLM: {llm_provider}")
    
    prompt = PromptTemplate.from_template('''
        Generate a list of search queries for a vector database based on customer inquiries about electronics.
        Use the chat history and context to retain all technical details and product names.
        The queries must always be written in Czech and formatted as a JSON object.
        Ensure that all generated queries are valid and match documents available in the vector database for product information retrieval.
        The output should contain multiple search queries to cover different possible interpretations of the customer’s request.

        Instructions:
            •	Interpret the customer inquiry to determine the relevant products or components that need information.
            •	Utilize past messages from the chat history to refine the queries.
            •	If the customer mentions a price, apply the corresponding price_min and price_max filters.
            •	The product_code field should remain empty.

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
    generated_search_queries = output_data["parsed"].search_queries
    
    # Count tokens
    token_manager = TokenManager()
    model_name = get_model_name(llm)
    input_tokens, output_tokens = _extract_token_counts(output_data)
    
    token_manager.add_token(model_name, input_tokens, output_tokens)
    
    for query_obj in generated_search_queries:
        if query_obj.min_price is not None:
            query_obj.min_price *= 0.85

        if query_obj.max_price is not None:
            query_obj.max_price *= 1.15

    product_code_pattern = r'^[A-Z](?=.*\d)[a-zA-Z0-9]{4,8}$'
        
    found_codes: List[str] = re.findall(product_code_pattern, customer_input, re.IGNORECASE)
    unique_codes: List[str] = sorted(list(set(found_codes)))
    
    if not unique_codes:
        print(f"V dotazu '{customer_input[:50]}...' nebyly nalezeny žádné kódy produktů.")

    print(f"Nalezeny unikátní kódy v dotazu '{customer_input[:50]}...': {unique_codes}")

    for code in unique_codes:
        new_query_object = SearchQuery(
            query=customer_input,
            product_code=code
        )
        generated_search_queries.append(new_query_object)
        print(f"  -> Vytvořen SearchQuery pro kód: {code}")
    
    basic_query_object = SearchQuery(
            query=customer_input
        )
    generated_search_queries.append(basic_query_object) # když se nám něco pokazí v generate search queries, tak abychom aspoň nějaké dokumenty našli... 
    
    output = Output(
        search_queries=generated_search_queries,
        token_manager=token_manager
    )
    
    return output
