from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv

from .config import OPENAI_MODEL, OPENAI_MINI_MODEL, GEMINI_MODEL, GEMINI_MINI_MODEL, ANTHROPIC_MODEL, ANTHROPIC_MINI_MODEL, XAI_MODEL, XAI_MINI_MODEL

# Načtení proměnných z .env souboru
load_dotenv()

class Models:
    openai = ChatOpenAI(
        model_name=OPENAI_MODEL,
        temperature=0,
    )

    openai_hot = ChatOpenAI(
        model_name=OPENAI_MODEL,
        temperature=0.7,
    )
    
    openai_mini = ChatOpenAI(
        model_name=OPENAI_MINI_MODEL,
        temperature=0,
    )
    
    openai_streaming = ChatOpenAI(
        model_name=OPENAI_MODEL,
        temperature=0,
        streaming=True
    )
    
    gemini = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0,
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    gemini_hot = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0.7,
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    gemini_mini = ChatGoogleGenerativeAI(
        model=GEMINI_MINI_MODEL,
        temperature=0,
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    anthropic = ChatAnthropic(
        model_name=ANTHROPIC_MODEL,
        temperature=0,
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    anthropic_hot = ChatAnthropic(
        model_name=ANTHROPIC_MODEL,
        temperature=0.7,
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    anthropic_mini = ChatAnthropic(
        model_name=ANTHROPIC_MINI_MODEL,
        temperature=0,
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    grok = ChatOpenAI(
        model=XAI_MODEL,
        temperature=0,
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY")
    )
    
    grok_hot = ChatOpenAI(
        model=XAI_MODEL,
        temperature=0.7,
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY")
    )

    grok_mini = ChatOpenAI(
        model=XAI_MINI_MODEL,
        temperature=0,
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY")
    )
