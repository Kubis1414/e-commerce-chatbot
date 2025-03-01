import streamlit as st
import os
from dotenv import load_dotenv
from promptflow.client import PFClient
from promptflow.entities import Run

# Načtení proměnných prostředí
load_dotenv()

# Inicializace PFClient
client = PFClient()

def main():
    st.title("E-commerce Chatbot")
    st.sidebar.title("Nastavení")
    
    # Nastavení v sidebaru
    st.sidebar.subheader("O aplikaci")
    st.sidebar.info("Tento chatbot pomáhá zákazníkům najít odpovědi na jejich dotazy ohledně produktů.")
    
    # Inicializace historie chatu, pokud neexistuje
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Zobrazení dosavadní historie chatu
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Vstupní pole pro dotaz uživatele
    if prompt := st.chat_input("Na co se chcete zeptat?"):
        # Přidání zprávy uživatele do historie
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Zobrazení zprávy uživatele
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Zobrazení indikátoru, že chatbot pracuje
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.text("Přemýšlím...")
            
            try:
                # Spuštění promptflow flow
                flow_inputs = {"user_query": prompt}
                flow_path = os.path.join(os.getcwd(), "flow")
                
                run = client.test(flow=flow_path, inputs=flow_inputs)
                response = run.outputs["final_answer"]
                
                # Aktualizace placeholderu s odpovědí
                message_placeholder.markdown(response)
                
                # Přidání odpovědi do historie
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_message = f"Došlo k chybě při zpracování vašeho dotazu: {str(e)}"
                message_placeholder.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
