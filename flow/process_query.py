from promptflow import tool
import os
from langchain_openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate

from langchain.chains import LLMChain
from dotenv import load_dotenv

# Načtení proměnných z .env souboru
load_dotenv()


@tool
def process_query(customer_input: str, chat_history: list) -> list[str]:
    """
    Extracts a search query from the user customer_input and chat_history
    """
    
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0
    )
    
    prompt = PromptTemplate.from_template("""
        Na základě následujícího dotazu zákazníka e-shopu extrahuj klíčová slova, která nejlépe vystihují, co zákazník hledá.
        Tato klíčová slova budou použita pro vyhledávání v databázi produktů.

        Dotaz zákazníka: "{{ user_query }}"

        Extrahuj pouze podstatná klíčová slova, která reprezentují:
        1. Typy produktů, které zákazník hledá
        2. Vlastnosti nebo funkce, které zákazník požaduje
        3. Značky nebo kategorie, které zákazník zmínil

        Výstup by měl být stručný (maximálně 10 slov) a obsahovat pouze klíčová slova oddělená mezerami, bez interpunkce.
    """)
    
    data = {
        "question": customer_input,
        "chat_history": chat_history
    }
    
    chain = prompt | llm
    output_data = chain.invoke(data)
    
    print(output_data)
    
    return search_query
