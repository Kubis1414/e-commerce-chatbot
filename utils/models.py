import os, json, requests
from typing import Any, List
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

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
        """Returns the appropriate model based on the specified provider and type.
        
        Args:
            provider: LLM provider ("GOOGLE", "XAI", "OPENAI", "ANTHROPIC")
            model_type: Type of model ("mini", "normal", "hot"), default is "normal"
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


class TokenCounter:
    def __init__(self, model: str="gpt-4o", input_tokens: int=0, output_tokens: int=0, note: str=""):
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.note = note


class TokenManager:
    """Manages token counting and cost calculation"""
    
    def __init__(self):
        self.tokens = []
        self.pricing_manager = PricingManager()
    
    def add_token(self, model: str, input_tokens: int, output_tokens: int, note: str="") -> None:
        """Add token usage to tracking"""

        self.tokens.append(TokenCounter(model, input_tokens, output_tokens, note))

    
    def calculate_total_cost(self) -> float:
        """Calculate the total cost of all tracked tokens"""
        return self.pricing_manager.calculate_cost(self.tokens)


class PricingManager:
    """Manages pricing data and calculates costs"""
    
    
    def __init__(self):
        self.cache_manager = PricingCacheManager()
    
    
    def calculate_cost(self, tokens: List[TokenCounter]) -> float:
        """Calculate cost based on tokens used"""
        pricing_data = self.cache_manager.get_current_pricing_data()
        usd_czk_rate = pricing_data.get("USD/CZK", 23)
        api_costs = pricing_data.get("api_costs", {})
        
        total_cost = 0
        for token in tokens:
            # Zpracování vstupních tokenů
            cost_key_input = self._get_cost_key(token.model, "Input")
            input_price = api_costs.get(cost_key_input, 3)
            if cost_key_input not in api_costs:
                print(f"Unknown input model pricing for {token.model}")
            
            # Zpracování výstupních tokenů
            cost_key_output = self._get_cost_key(token.model, "Output")
            output_price = api_costs.get(cost_key_output, 15)
            if cost_key_output not in api_costs:
                print(f"Unknown output model pricing for {token.model}")
            
            # Výpočet ceny pro aktuální token
            token_cost = (token.input_tokens * input_price + token.output_tokens * output_price) / 1_000_000
            total_cost += token_cost
        
        return round(usd_czk_rate * total_cost, 5)


    def _get_cost_key(self, model: str, token_type: str) -> str:
        """Convert model name to cost key used in pricing data"""
        # Convert model names like "gpt-4o" to cost keys like "gpt_4o_input"
        model_key = model.replace("-", "_").replace(".", "_")
        
        return f"{model_key}_{token_type.lower()}"

class PricingCacheManager:
    """Manages caching of pricing data"""
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pricing_cache')
    os.makedirs(output_dir, exist_ok=True)

    file_name = 'pricing_cache.json'
    file_path = os.path.join(output_dir, file_name)
    
    def get_usd_czk_exchange_rate(self, date) -> float:
        """Returns the USD/CZK exchange rate for a specific day. We call the kurzy.cz API to query the ČNB exchange rate."""
        try:
            url = f'https://data.kurzy.cz/json/meny/b[6]den[{date}].json'  # b6 je banka 6, což je ČNB
            response = requests.get(url, timeout=5)  # Adding timeout for the request
            response.raise_for_status()  # Raises exception for 4XX/5XX responses
            
            exchange_rates = response.json()
            usd_czk_rate = exchange_rates['kurzy']['USD']['dev_stred']  # vezmeme USD/CZK kurz a devizový střed
            return usd_czk_rate
            
        except requests.exceptions.Timeout:
            print(f"Požadavek na API vypršel pro datum {date}.")
            return 23
        except requests.exceptions.ConnectionError:
            print(f"Nepodařilo se připojit k API pro datum {date}.")
            return 23
        except requests.exceptions.HTTPError as err:
            print(f"HTTP chyba při získávání dat pro datum {date}: {err}")
            return 23
        except requests.exceptions.RequestException as err:
            print(f"Obecná chyba požadavku pro datum {date}: {err}")
            return 23
        except (KeyError, ValueError, TypeError) as err:
            print(f"Chyba při zpracování dat z API pro datum {date}: {err}")
            return 23


    def read_from_file(self, file_path):
        # vytvoření cesty ke cachovacímu jsonu, abychom nemuseli pořád provolávat tu API
   
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return None
    
    
    def get_api_costs(self) -> dict:
        """Returns a dictionary with prices for various models for using their API. Price per 1 million tokens in dollars!"""
        
        # prices are in $ for 1M tokens
        api_costs = {
            "gpt_4o_input": 2.5,
            "gpt_4o_output": 10,
            "gpt_4o_mini_input": 0.15,
            "gpt_4o_mini_output": 0.6,
            "claude_3_7_sonnet_latest_input": 3,
            "claude_3_7_sonnet_latest_output": 15,
            "claude_3_5_haiku_latest_input": 1,
            "claude_3_5_haiku_latest_output": 5,
            "models/gemini_2_0_flash_input": 0.1,
            "models/gemini_2_0_flash_output": 0.4,
            "models/gemini_2_0_flash_lite_input": 0.075,
            "models/gemini_2_0_flash_lite_output": 0.3,
            "grok_2_latest_input": 2,
            "grok_2_latest_output": 10,
        }
        
        return api_costs


    def get_today_date_formatted(self) -> str:
        """Return today's date in format YYYYMMDD"""
        today = datetime.today()
        formatted_date = today.strftime('%Y%m%d')
        
        return formatted_date
    

    def get_current_pricing_data(self) -> dict:
        """Get the current pricing data, refreshing if needed"""

        today = self.get_today_date_formatted()
        cached_data = self.read_from_file(self.file_path)
        
        if cached_data:
            if cached_data.get("date") == today:
                # dnes se aktualizovali cached_data, můžeme ceny načíst z nich
                print("Cashed data, načítáme ze souboru")
                return cached_data
                
            else:
                print("Aktualizace cached dat")
                new_price_data = self.update_cached_data(today)
                return new_price_data

        else:
            print("Žádné cached data, vytvářím...")
            new_price_data = self.update_cached_data(today)
            return new_price_data


    def update_cached_data(self, today) -> dict:
        """Update the pricing data and write it to the cache json file"""
        price_data = {}
        
        try:
            usd_czk_rate = self.get_usd_czk_exchange_rate(today)
            api_costs = self.get_api_costs()
            
            price_data = {
                "date": today,
                "USD/CZK": usd_czk_rate,
                "api_costs": api_costs
            }
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(price_data, f, indent=4)
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
        except KeyError as e:
            print(f"Error processing data: {e}")

        return price_data


# Helper function to get model name from different LLM types
def get_model_name(llm) -> str:
    """Get model name from different types of LLM objects"""
    
    if hasattr(llm, "model_name"):
        return llm.model_name
    elif hasattr(llm, "model"):
        return llm.model
    else:
        raise ValueError("Neznámý typ LLM")


def _extract_token_counts(output_data: Any) -> tuple[int, int]:
        """Extract token counts from output data"""
        input_tokens = 0
        output_tokens = 0

        # Získání raw části dat
        if isinstance(output_data, dict):
            raw = output_data.get("raw", None)
        else:
            raw = output_data
        
        usage_metadata = getattr(raw, "usage_metadata", {})
        
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
  
        return input_tokens, output_tokens
