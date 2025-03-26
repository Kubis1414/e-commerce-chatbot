from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
import os
from dotenv import load_dotenv

from .config import OPENAI_MODEL, OPENAI_MINI_MODEL, GOOGLE_MODEL, GOOGLE_BASIC_MODEL, ANTHROPIC_MODEL, ANTHROPIC_BASIC_MODEL, XAI_MODEL, XAI_BASIC_MODEL

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
        model=GOOGLE_MODEL,
        temperature=0,
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    gemini_hot = ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=0.7,
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    gemini_mini = ChatGoogleGenerativeAI(
        model=GOOGLE_BASIC_MODEL,
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
        model_name=ANTHROPIC_BASIC_MODEL,
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
        model=XAI_BASIC_MODEL,
        temperature=0,
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY")
    )


    def get_model(provider: str, model_type: str = "normal"):
        """Vrátí příslušný model podle zadaného poskytovatele a typu.
        
        Args:
            provider: Poskytovatel LLM ("GOOGLE", "XAI", "OPENAI", "ANTHROPIC")
            model_type: Typ modelu ("mini", "normal", "hot"), výchozí je "normal"
        """
        provider_map = {
            "GOOGLE": {
                "mini": Models.gemini_mini,
                "normal": Models.gemini,
                "hot": Models.gemini_hot
            },
            "XAI": {
                "mini": Models.grok_mini,
                "normal": Models.grok,
                "hot": Models.grok_hot
            },
            "OPENAI": {
                "mini": Models.openai_mini,
                "normal": Models.openai,
                "hot": Models.openai_hot
            },
            "ANTHROPIC": {
                "mini": Models.anthropic_mini,
                "normal": Models.anthropic,
                "hot": Models.anthropic_hot
            }
        }
        
        if provider not in provider_map:
            return None
            
        return provider_map[provider].get(model_type)
