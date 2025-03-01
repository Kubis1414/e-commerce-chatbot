from promptflow import tool
from promptflow.connections import OpenAIConnection
import os
import openai
import json
from typing import List, Dict
from jinja2 import Template

@tool
def filter_docs(retrieved_docs: List[Dict], user_query: str) -> List[Dict]:
    """
    Filters the retrieved documents to get the top 10 most relevant ones.
    """
    # Načtení promptu
    with open(os.path.join(os.path.dirname(__file__), "prompts", "doc_filter.jinja2"), "r", encoding="utf-8") as f:
        prompt_template = Template(f.read())
    
    # Sestavení promptu
    docs_json = json.dumps(retrieved_docs, ensure_ascii=False)
    prompt = prompt_template.render(user_query=user_query, documents=docs_json)
    
    # Získání OpenAI connection z promptflow
    conn = OpenAIConnection.get_connection("openai_connection")
    client = openai.OpenAI(api_key=conn.api_key)
    
    # Volání OpenAI API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi asistent pro filtrování relevantních dokumentů pro e-shop."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    # Extrakce filtrovaných dokumentů
    try:
        filtered_docs_json = response.choices[0].message.content.strip()
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
