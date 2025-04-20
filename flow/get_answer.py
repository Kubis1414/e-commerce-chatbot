from promptflow.core import tool
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts.prompt import PromptTemplate

from utils.models import Models, get_model_name, _extract_token_counts, TokenManager
from utils.weaviate_service import Document


class Product(BaseModel):
    """Product model."""

    name: str = Field(description="Name of the product.")
    description: str = Field(description="Very vert short description of the product.")
    price: float = Field(description="Price of the product.")
    product_code: str = Field(description="Product code of the product.")
    url: str = Field(description="URL of the product.")
    image_url: str = Field(description="URL of the product image.")


class OutputSchema(BaseModel):
    """Output schema for the LLM that generates answer to the customer question."""

    answer: str = Field(description="Answer to the customer question.")
    recommended_products: List[Product] = Field(default_factory=list, description="List of products that are recommended to the customer based on the question.")


class Output(BaseModel):
    """Output schema for the LLM that generates answer to the customer question."""

    response: OutputSchema = Field(default_factory=OutputSchema, description="Response from the LLM.")
    chat_history: list = Field(default_factory=list, description="Chat history of the conversation.")  
    context: dict = Field(default_factory=dict, description="Context of the conversation.")
    customer: dict = Field(default_factory=dict, description="Customer information.")
    search_queries: list = Field(default_factory=list, description="Search queries for the vector database.")
    cost: float = Field(description="Cost of the message that was generated for the customer.")


@tool
def get_answer(customer_input: str, documents: List[Document], context: dict, customer: dict, chat_history: list, llm_provider: str, search_queries: list, token_manager: TokenManager) -> dict:
    llm = Models.get_model(llm_provider, "hot")
    if not llm:
        raise ValueError(f"Nepodporovaný poskytovatel LLM: {llm_provider}")
    
    prompt = PromptTemplate.from_template('''
        You are a helpful customer service assistant for an e-commerce company.
        Your task is to provide accurate and relevant responses to customer inquiries.

    When generating a list of recommended products, follow these guidelines:
        -	Title: Provide a very short product title (maximum 6 words).
        -	Description: Include a short, clear product description.
        -	Product Code: Fill in the exact product code (e.g., “NL250b1a1a” or “JA0ws84”).
        -	URL: Provide the products URL.
        -	Image URL: Leave this field empty.
        -	By default, include 3 to 4 products in the recommended products list unless the customer specifies otherwise.

    Instructions:
        -   Use the provided context, documents, and chat history to generate a complete and relevant response.
        -	Maintain a friendly and professional tone.
        -	If customer information is available, personalize the response using their name (vocative form).
        -	DO NOT greet the customer!
        -	Recommend only relevant products based on the inquiry.
        -	Always respond in Czech.
        -	Format product recommendations clearly, following the response structure.
        -   The reccommended products must also be mentioned in the answer.

    Context:
        -	General context: {context}
        -	Customer details: {customer}
        -	Chat history: {chat_history}
        -	Relevant documents: {documents}
        -	Customer inquiry: {customer_input}

        Always provide a response in the following format:
            "answer": "Your response in Czech",
            "recommended_products": []
    ''')
    
    data = {
        "customer_input": customer_input,
        "chat_history": chat_history[:7],
        "documents": documents,
        "context": context,
        "customer": customer
    }
    
    structured_llm = llm.with_structured_output(OutputSchema, include_raw=True)
    chain = prompt | structured_llm
    
    output_data = chain.invoke(data)
    response = output_data.get("parsed")
    answer = response.answer
    
    # Count tokens
    model_name = get_model_name(llm)
    input_tokens, output_tokens = _extract_token_counts(output_data)
    
    token_manager.add_token(model_name, input_tokens, output_tokens)
    
    chat_history.append({
        "customer_input": customer_input,
        "assistant_answer": {
            "answer": answer,
            "recommended_products": response.recommended_products
        }
    })
    
    cost = token_manager.calculate_total_cost()
    
    response_dict = response.model_dump()

    if response_dict["recommended_products"] and isinstance(response_dict["recommended_products"], list):
        for product in response_dict["recommended_products"]:
            product_code = product["product_code"]

            # Zkontrolujeme, zda product_code existuje a je to neprázdný string
            if product_code and isinstance(product_code, str) and product_code.strip():
                image_url = f"https://image.alza.cz/products/{product_code}/{product_code}.jpg?width=500&height=500"
                product["image_url"] = image_url # Přidáme URL obrázku do dict produktu

    output = Output(
        response=response_dict,
        chat_history=chat_history,
        context=context,
        customer=customer,
        search_queries=search_queries,
        cost=cost
    )

    print(output.model_dump_json(indent=2))
    return output.model_dump()
