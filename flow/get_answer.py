from promptflow.core import tool
from typing import List
from pydantic import BaseModel, Field
from langchain.prompts.prompt import PromptTemplate

from utils.models import Models, get_model_name, _extract_token_counts, TokenManager
from utils.weaviate_service import Document


class Product(BaseModel):
    """Product model."""

    name: str = Field(description="Name of the product.")
    description: str = Field(description="Description of the product.")
    price: float = Field(description="Price of the product.")
    image_url: str = Field(description="Image URL of the product.")
    url: str = Field(description="URL of the product.")


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
    llm = Models.get_model(llm_provider)
    if not llm:
        raise ValueError(f"Nepodporovaný poskytovatel LLM: {llm_provider}")
    
    prompt = PromptTemplate.from_template('''
        You are a helpful customer service assistant for an e-commerce company. Your task is to provide helpful and accurate responses to customer inquiries.

        Instructions:
        - Use the provided context, documents, and chat history to generate a comprehensive response
        - Maintain a friendly and professional tone
        - If customer information is available, personalize the response using their name/vokative
        - Recommend relevant products when appropriate
        - Always respond in Czech language
        - Format product recommendations clearly with name, description, price and URL
        - Keep responses concise but informative

        Context:
        {context}

        Customer Information:
        {customer}

        Chat History:
        {chat_history}

        Relevant Documents:
        {documents}

        Customer Inquiry:
        {customer_input}

        Always provide a response in the following format:
            "answer": "Your response in Czech",
            "recommended_products": []
    ''')
    
    data = {
        "customer_input": customer_input,
        "chat_history": chat_history,
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
    
    chat_history.append({"customer_input": customer_input, "assistant_answer": answer})
    
    cost = token_manager.calculate_total_cost()
    
    output = Output(
        response=response.model_dump(),
        chat_history=chat_history,
        context=context,
        customer=customer,
        search_queries=search_queries,
        cost=cost
    )
    
    print(output.model_dump())
    
    return output.model_dump()
