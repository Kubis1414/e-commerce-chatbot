from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.utils.utils import secret_from_env

from .config import OPENAI_MODEL, OPENAI_MINI_MODEL, GEMINI_MODEL, GEMINI_MINI_MODEL, ANTHROPIC_MODEL, ANTHROPIC_MINI_MODEL, XAI_MODEL, XAI_MINI_MODEL


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
        model = GEMINI_MODEL,
        temperature=0
    )
    
    gemini_hot = ChatGoogleGenerativeAI(
        model = GEMINI_MODEL,
        temperature=0.7
    )
    
    gemini_mini = ChatGoogleGenerativeAI(
        model = GEMINI_MINI_MODEL,
        temperature=0
    )
    
    anthropic = ChatAnthropic(
        model_name=ANTHROPIC_MODEL,
        temperature=0,
    )
    
    anthropic_hot = ChatAnthropic(
        model_name=ANTHROPIC_MODEL,
        temperature=0.7,
    )
    
    anthropic_mini = ChatAnthropic(
        model_name=ANTHROPIC_MINI_MODEL,
        temperature=0,
    )
    
    grok = ChatOpenAI(
        model=XAI_MODEL,
        temperature=0,
        base_url="https://api.x.ai/v1",
        api_key=secret_from_env("XAI_API_KEY")
    )
    
    grok_hot = ChatOpenAI(
        model=XAI_MODEL,
        temperature=0.7,
        base_url="https://api.x.ai/v1",
        api_key=secret_from_env("XAI_API_KEY")
    )

    grok_mini = ChatOpenAI(
        model=XAI_MINI_MODEL,
        temperature=0,
        base_url="https://api.x.ai/v1",
        api_key=secret_from_env("XAI_API_KEY")
    )
