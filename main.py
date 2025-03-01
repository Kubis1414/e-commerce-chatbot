import streamlit as st
import openai
import requests
import os

# Pseudoknihovna pro vektorovou DB (zde jen jako příklad)
class FakeVectorDB:
    def search(self, query_embedding, top_k=50):
        """
        V reálu by se sem posílal embedding dotazu a 
        skutečně by se hledalo v DB. My tady předstíráme,
        že vracíme 50 (mírně) relevantních dokumentů.
        """
        # Fake data - v produkci by to byly reálné dokumenty
        docs = [f"Dokument_{i}" for i in range(50)]
        return docs

    def embed_text(self, text):
        """
        Taky fejk. Tady by se z textu vygeneroval embedding,
        např. voláním OpenAI nebo jiného modelu.
        """
        return [0.042] * 768  # dummy embedding

# Inicializace vektorové DB
vector_db = FakeVectorDB()

openai.api_key = os.environ.get("OPENAI_API_KEY")

def create_search_query(user_question):
    """
    Prompt, který z uživatelského vstupu vytvoří vyhledávací dotaz.
    Můžeš sem hodit GPT, abys z user_question extrahoval klíčová slova.
    Tady radši text napevno, pro ilustraci.
    """
    prompt = (f"Uživatel se ptá: {user_question}\n"
              "Vytvoř vyhledávací dotaz (max 10 slov) relevantní k tématu.")
    try:
        # volání OpenAI completions (příklad s GPT-3.5)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=30,
            temperature=0.7
        )
        search_query = response.choices[0].text.strip()
        return search_query
    except Exception as e:
        st.error(f"Nepovedlo se vygenerovat vyhledávací dotaz: {e}")
        return None

def reduce_documents(docs, user_question):
    """
    Prompt, který z vybraných 50 dokumentů vybere 10 nejrelevantnějších.
    Opět by se to dalo řešit i rankováním pomocí embeddingů,
    ale ukázkově si můžeme demonstrovat GPT-based approach.
    """
    # Předáváme GPT seznam doc stringů a ptáme se, které jsou nejrelevantnější
    doc_list_str = "\n".join(docs)
    prompt = (
        f"Zde je seznam dokumentů:\n{doc_list_str}\n\n"
        f"Uživatel se ptá: {user_question}\n"
        "Vyber 10 nejrelevantnějších IDs dokumentů z výše uvedeného seznamu. "
        "Dávej pozor, aby sis nevymýšlel neexistující položky!"
    )
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        selected_docs = response.choices[0].text.strip()
        # Nyní bychom v reálu extrahovali ID dokumentů a vrátili je jako list
        # Pro ukázku to necháme v textové podobě
        return selected_docs
    except Exception as e:
        st.error(f"Nepovedlo se zredukovat dokumenty: {e}")
        return None

def generate_final_answer(reduced_docs, user_question):
    """
    Finální prompt, který převezme top 10 dokumentů
    a zkusí vytvořit finální odpověď pro uživatele.
    """
    prompt = (
        f"Představ si, že jsi chytrý AI asistent pro e-shop. "
        f"Toto je dotaz uživatele: {user_question}\n\n"
        f"Toto je top 10 relevantních dokumentů:\n{reduced_docs}\n\n"
        "Využij dokumenty a své znalosti, abys vytvořil věcnou a přesnou odpověď.\n"
        "Pokud informace chybí, co nejlépe je odhadni a vysvětli uživateli, "
        "že se nejedná o 100% ověřené informace."
    )
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        final_answer = response.choices[0].text.strip()
        return final_answer
    except Exception as e:
        st.error(f"Nepovedlo se vygenerovat odpověď: {e}")
        return None

def main():
    st.title("Chatbot eCommerce - Promptflow (pseudo-demo)")
    st.write("Prosím, zadej svůj dotaz:")  
    user_question = st.text_input("Dotaz", value="")
    
    if st.button("Odeslat dotaz"):
        if not user_question:
            st.warning("Nejdřív sem něco napiš, potom klikej na tlačítka.")
        else:
            # 1) Prompt - vygenerovat vyhledávací dotaz
            search_query = create_search_query(user_question)
            if not search_query:
                return
            
            # 2) Vyhledání ve vektorové DB
            query_embedding = vector_db.embed_text(search_query)
            docs = vector_db.search(query_embedding, top_k=50)
            
            # 3) Redukce dokumentů
            top_10_docs = reduce_documents(docs, user_question)
            if not top_10_docs:
                return
            
            # 4) Finální odpověď
            answer = generate_final_answer(top_10_docs, user_question)
            if answer:
                st.success(answer)

if __name__ == "__main__":
    main()