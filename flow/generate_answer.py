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
def generate_answer(user_query: str, filtered_docs: List[Dict]) -> str:
    """
    Generates the final answer based on the filtered documents and the user query.
    """
    # Načtení promptu
    with open(os.path.join(os.path.dirname(__file__), "prompts", "answer_generation.jinja2"), "r", encoding="utf-8") as f:
        prompt_template_content = f.read()
    
    # Vytvoření LangChain chat modelu
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.5
    )
    
    # Vytvoření LangChain promptu
    docs_json = json.dumps(filtered_docs, ensure_ascii=False)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Jsi asistent pro e-shop, který pomáhá zákazníkům s jejich dotazy. Komunikuješ v přátelském, ale profesionálním tónu."),
        ("human", prompt_template_content)
    ])
    
    # Vytvoření a spuštění chainu
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.invoke({"user_query": user_query, "documents": docs_json})
    
    # Získání odpovědi
    answer = response["text"].strip()
    
    return answer
