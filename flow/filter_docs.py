from promptflow import tool
import os
import json
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Načtení proměnných z .env souboru
load_dotenv()

@tool
def filter_docs(retrieved_docs: List[Dict], user_query: str) -> List[Dict]:
    """
    Filters the retrieved documents to get the top 10 most relevant ones.
    """
    # Načtení promptu
    with open(os.path.join(os.path.dirname(__file__), "prompts", "doc_filter.jinja2"), "r", encoding="utf-8") as f:
        prompt_template_content = f.read()
    
    # Vytvoření LangChain chat modelu
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.2
    )
    
    # Vytvoření LangChain promptu
    docs_json = json.dumps(retrieved_docs, ensure_ascii=False)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Jsi asistent pro filtrování relevantních dokumentů pro e-shop."),
        ("human", prompt_template_content)
    ])
    
    # Vytvoření a spuštění chainu
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({"user_query": user_query, "documents": docs_json})
    
    # Extrakce filtrovaných dokumentů
    try:
        filtered_docs_json = response["text"].strip()
        # Extrakce JSON z odpovědi (může být obklopeno vysvětlujícím textem)
        start_idx = filtered_docs_json.find('[')
        end_idx = filtered_docs_json.rfind(']') + 1
        if start_idx >= 0 and end_idx > start_idx:
            filtered_docs_json = filtered_docs_json[start_idx:end_idx]
        
        filtered_docs = json.loads(filtered_docs_json)
        
        # Omezení na top 10 dokumentů
        filtered_docs = filtered_docs[:10]
    except:
        # V případě chyby vrátíme prvních 10 dokumentů z původní sady
        filtered_docs = retrieved_docs[:10]
    
    return filtered_docs
