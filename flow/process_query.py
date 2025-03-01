from promptflow import tool
from promptflow.connections import OpenAIConnection
import os
import openai
from jinja2 import Template

@tool
def process_query(user_query: str) -> str:
    """
    Extracts a search query from the user question.
    """
    # Načtení promptu
    with open(os.path.join(os.path.dirname(__file__), "prompts", "query_extraction.jinja2"), "r", encoding="utf-8") as f:
        prompt_template = Template(f.read())
    
    # Sestavení promptu
    prompt = prompt_template.render(user_query=user_query)
    
    # Získání OpenAI connection z promptflow
    conn = OpenAIConnection.get_connection("openai_connection")
    client = openai.OpenAI(api_key=conn.api_key)
    
    # Volání OpenAI API
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Jsi asistent pro extrakci klíčových slov z dotazů zákazníků e-shopu."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    # Extrakce search query
    search_query = response.choices[0].message.content.strip()
    
    return search_query
