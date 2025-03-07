import streamlit as st
from promptflow import PFClient
from components.ProductCarousel import product_carousel

# Inicializace Streamlit
st.set_page_config(layout="wide")

# Inicializace chat historie v session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "context" not in st.session_state:
    st.session_state.context = {}

if "customer" not in st.session_state:
    st.session_state.customer = {}

if "customer_message" not in st.session_state:
    st.session_state.customer_message = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "language" not in st.session_state:
    st.session_state.language = "CS"

if "selected_page_index" not in st.session_state:
    st.session_state.selected_page_index = 0

# Přednastavené hodnoty
CUSTOMER_IDS = ["CUS765894089", "CUS905621345", "CUS168925307", "CUS788902345", "CUS630952341", "anonymous"]

# Vytvoření párů title-url pro synchronizaci
PAGE_DATA = [
    {
        "title": "Domů - E-shop s elektronikou",
        "url": "https://eshop.cz/"
    },
    {
        "title": "Mobilní telefon iPhone 15 Pro Max",
        "url": "https://eshop.cz/mobily/iphone-15-pro-max"
    },
    {
        "title": "Notebooky MacBook Pro M1 Pro",
        "url": "https://eshop.cz/notebooky/macbook-pro-m1-pro"
    },
    {
        "title": 'Televize Samsung 8K 75"',
        "url": 'https://eshop.cz/televize/samsung-8k-75'
    },
    {
        "title": "Kontakt a podpora",
        "url": "https://eshop.cz/kontakt"
    }
]

# Získání seznamů titles a urls přímo z PAGE_DATA
PAGE_TITLES = [page["title"] for page in PAGE_DATA]
URLS = [page["url"] for page in PAGE_DATA]

LANGUAGES = {
    "CS": "Čeština",
    "SK": "Slovenština",
    "EN": "Angličtina",
    "DE": "Němčina"
}

# Mapování LLM providerů
LLM_PROVIDERS = {
    "GOOGLE": "Google Gemini",
    "XAI": "XAI Grok",
    "OPENAI": "OpenAI GPT",
    "ANTHROPIC": "Anthropic Claude"
}

# Inicializace LLM providera v session state pokud neexistuje
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "GOOGLE"

# Vytvoření layoutu
with st.sidebar:
    with st.expander("Nastavení", expanded=True):
        # Context editor
        st.write("Context")
        
        # Synchronizované selectboxy
        selected_title_index = PAGE_TITLES.index(st.selectbox("Page Title", PAGE_TITLES, key="context_page_title", index=st.session_state.selected_page_index))
        st.session_state.selected_page_index = selected_title_index
        
        # URL se automaticky aktualizuje podle vybraného titulku
        context_current_url = URLS[selected_title_index]
                
        # Language selector
        selected_language = st.selectbox(
            "Jazyk komunikace",
            options=list(LANGUAGES.keys()), 
            format_func=lambda x: LANGUAGES[x],
            key="language"
        )
        
        st.session_state.context = {
            "page_title": PAGE_TITLES[selected_title_index],
            "current_url": context_current_url,
            "language": st.session_state.language,
        }
        
        # Customer editor
        st.write("Customer")
        customer_id = st.selectbox(
            "Customer ID",
            options=CUSTOMER_IDS,
            key="customer_id",
            format_func=lambda x: "Nepřihlášený zákazník" if x == "anonymous" else x
        )

        st.session_state.customer = {
            "customer_id": customer_id
        }
        
        # LLM Provider selector
        selected_provider = st.selectbox(
            "LLM Provider",
            options=list(LLM_PROVIDERS.keys()),
            format_func=lambda x: LLM_PROVIDERS[x],
            key="llm_provider"
        )

st.title("Chat s e-commerce AI asistenkou")

chat_container = st.container()
with chat_container:
    # Vytvoření scrollovatelného kontejneru pro chat
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        # Zobrazení chat historie
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# Chat input zůstává pod scrollovatelnou oblastí
if customer_message := st.chat_input("Napište svoji zprávu..."):
    # Přidání uživatelské zprávy do historie
    st.session_state.customer_message = customer_message
    st.session_state.messages.append({"role": "user", "content": customer_message})
    with st.chat_message("user"):
        st.markdown(customer_message)

    try:
        pf = PFClient()
        
        # Příprava dat pro flow
        flow_inputs = {
            "customer_input": st.session_state.customer_message,
            "chat_history": st.session_state.chat_history,
            "context": st.session_state.context,
            "customer": st.session_state.customer,
            "llm_provider": st.session_state.llm_provider
        }
        
        # Spuštění flow
        flow_result = pf.test(flow="flow", inputs=flow_inputs)
        
        # Získání outputů z flow
        assistant_response = flow_result["response"]["answer"]
        recommended_products = flow_result["response"]["recommended_products"]
        st.session_state.chat_history = flow_result["chat_history"]
        st.session_state.context = flow_result["context"]
        st.session_state.customer = flow_result["customer"]
        
        # Přidání odpovědi asistenta do historie
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        with st.chat_message("assistant"):
            st.markdown(assistant_response)
            
            # Zobrazení doporučených produktů, pokud nějaké jsou
            if recommended_products:
                product_carousel(recommended_products)
            
    except Exception as e:
        st.error(f"Došlo k chybě při zpracování požadavku: {str(e)}")

# Debug informace v sidebaru
with st.sidebar:
    if st.checkbox("Zobrazit debug informace"):
        st.write("Context:", st.session_state.context)
        st.write("Customer:", st.session_state.customer)
        st.write("Chat History:", st.session_state.chat_history)
