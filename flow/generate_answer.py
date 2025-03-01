from promptflow import tool
from promptflow.connections import OpenAIConnection
import os
import openai
import json
from typing import List, Dict
from jinja2 import Template

@tool
def generate_answer(user_query: str, filtered_docs: List[Dict]) -> str:
    """
    Generates the final answer based on the filtered documents and the user query.
    """
    # Načtení promptu
    with open(os.path.join(os.path.dirname(__file__), "prompts", "answer_generation.jinja2"), "r", encoding="utf-8") as f:
        prompt_template = Template(f.read())
    
    # Sestavení promptu
    docs_json = json.dumps(filtered_docs, ensure_ascii=False)
    prompt = prompt_template.render(user_query=user_query, documents=docs_json)
    
    # Získání OpenAI connection z promptflow
    conn = OpenAIConnection.get_connection("openai_connection")
    client = openai.OpenAI(api_key=conn.api_key)
    
    # Volání OpenAI API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi asistent pro e-shop, který pomáhá zákazníkům s jejich dotazy. Komunikuješ v přátelském, ale profesionálním tónu."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    
    # Získání odpovědi
    answer = response.choices[0].message.content.strip()
    
    return answer
