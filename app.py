import streamlit as st
import json
from promptflow import PFClient
from promptflow.entities import AzureOpenAIConnection
import os
from datetime import datetime

# Inicializace Streamlit
st.set_page_config(layout="wide")

# Inicializace chat historie v session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "context" not in st.session_state:
    st.session_state.context = {}

if "customer" not in st.session_state:
    st.session_state.customer = {}

# Vytvoření layoutu se dvěma sloupci
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Nastavení")
    
    # Context editor
    st.write("Context")
    context_page_title = st.text_input("Page Title", key="context_page_title")
    context_current_url = st.text_input("Current URL", key="context_current_url")
    
    if context_page_title or context_current_url:
        st.session_state.context = {
            "page_title": context_page_title,
            "current_url": context_current_url
        }
    
    # Customer editor
    st.write("Customer")
    customer_id = st.text_input("Customer ID", key="customer_id")
    customer_name = st.text_input("Name", key="customer_name")
    customer_email = st.text_input("Email", key="customer_email")
    customer_vokative = st.text_input("Vokativ", key="customer_vokative")
    
    if customer_id:
        st.session_state.customer = {
            "customer_id": customer_id,
            "name": customer_name,
            "email": customer_email,
            "vokative": customer_vokative
        }
        # Odstranění prázdných hodnot
        st.session_state.customer = {k: v for k, v in st.session_state.customer.items() if v}

with col1:
    st.title("Chat s AI Asistentem")
    
    # Zobrazení chat historie
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Napište svoji zprávu..."):
        # Přidání uživatelské zprávy do historie
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            # Inicializace PFClient
            pf = PFClient()
            
            # Příprava dat pro flow
            flow_inputs = {
                "user_query": prompt,
                "chat_history": [{"role": m["role"], "content": m["content"]} 
                               for m in st.session_state.messages[:-1]],  # Bez poslední zprávy
                "context": st.session_state.context,
                "customer": st.session_state.customer
            }
            
            # Spuštění flow
            flow_result = pf.test(flow="flow", inputs=flow_inputs)
            
            # Získání odpovědi z flow
            assistant_response = flow_result["final_answer"]
            
            # Přidání odpovědi asistenta do historie
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
                
        except Exception as e:
            st.error(f"Došlo k chybě při zpracování požadavku: {str(e)}")
            
    # Debug informace
    if st.checkbox("Zobrazit debug informace"):
        st.write("Context:", st.session_state.context)
        st.write("Customer:", st.session_state.customer)
        st.write("Messages:", st.session_state.messages)
