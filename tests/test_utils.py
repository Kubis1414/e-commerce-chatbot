# tests/test_utils.py
import requests
import pytest
from unittest.mock import MagicMock, patch
import os
import json
from datetime import datetime

# Assuming utils.models is importable from the tests directory
# Adjust the import path if necessary based on your project structure and how pytest is run
from utils.models import (
    TokenCounter,
    TokenManager,
    PricingManager,
    PricingCacheManager,
    Models,
    get_model_name,
    _extract_token_counts
)
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# --- Tests for TokenCounter ---

def test_token_counter_initialization():
    """Test initialization of TokenCounter"""
    counter = TokenCounter(model="gpt-4o", input_tokens=100, output_tokens=200, note="test note")
    assert counter.model == "gpt-4o"
    assert counter.input_tokens == 100
    assert counter.output_tokens == 200
    assert counter.note == "test note"

# --- Tests for get_model_name ---

def test_get_model_name_openai():
    """Test get_model_name with ChatOpenAI"""
    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.model_name = "gpt-4o-test"
    assert get_model_name(mock_llm) == "gpt-4o-test"

def test_get_model_name_google():
    """Test get_model_name with ChatGoogleGenerativeAI"""
    mock_llm = MagicMock(spec=ChatGoogleGenerativeAI)
    mock_llm.model = "gemini-test"
    assert get_model_name(mock_llm) == "gemini-test"

def test_get_model_name_anthropic():
    """Test get_model_name with ChatAnthropic"""
    mock_llm = MagicMock(spec=ChatAnthropic)
    mock_llm.model_name = "claude-test"
    assert get_model_name(mock_llm) == "claude-test"

def test_get_model_name_unknown():
    """Test get_model_name with an unknown LLM type"""
    mock_llm = object() # An object without model_name or model
    with pytest.raises(ValueError, match="Neznámý typ LLM"):
        get_model_name(mock_llm)

# --- Tests for _extract_token_counts ---

def test_extract_token_counts_dict():
    """Test _extract_token_counts with dictionary input"""
    output_data = {
        "raw": MagicMock(usage_metadata={"input_tokens": 50, "output_tokens": 150})
    }
    input_tokens, output_tokens = _extract_token_counts(output_data)
    assert input_tokens == 50
    assert output_tokens == 150

def test_extract_token_counts_object():
    """Test _extract_token_counts with object input"""
    output_data = MagicMock(usage_metadata={"input_tokens": 10, "output_tokens": 20})
    input_tokens, output_tokens = _extract_token_counts(output_data)
    assert input_tokens == 10
    assert output_tokens == 20

def test_extract_token_counts_missing_metadata():
    """Test _extract_token_counts when usage_metadata is missing"""
    output_data = MagicMock(spec=[]) # No usage_metadata attribute
    input_tokens, output_tokens = _extract_token_counts(output_data)
    assert input_tokens == 0
    assert output_tokens == 0

def test_extract_token_counts_missing_tokens():
    """Test _extract_token_counts when tokens are missing in metadata"""
    output_data = MagicMock(usage_metadata={}) # Empty metadata
    input_tokens, output_tokens = _extract_token_counts(output_data)
    assert input_tokens == 0
    assert output_tokens == 0

def test_extract_token_counts_dict_missing_raw():
    """Test _extract_token_counts with dict missing 'raw' key"""
    output_data = {}
    input_tokens, output_tokens = _extract_token_counts(output_data)
    assert input_tokens == 0
    assert output_tokens == 0

# --- Placeholder for future tests ---

# TODO: Add tests for PricingCacheManager (requires mocking requests and file I/O)
# TODO: Add tests for PricingManager (requires mocking PricingCacheManager or providing fixed data)
# TODO: Add tests for PricingManager (requires mocking PricingCacheManager or providing fixed data)
# TODO: Add tests for Models.get_model (might require mocking model initializations)


# --- Fixtures for TokenManager Tests ---

@pytest.fixture
def mock_token_manager():
    """Fixture to create a TokenManager instance with a mocked pricing manager."""
    with patch('utils.models.PricingManager') as MockPricingManager:
        # Configure the mock pricing manager instance
        mock_pricing_instance = MockPricingManager.return_value
        # Set a specific return value for calculate_cost for predictability
        mock_pricing_instance.calculate_cost.return_value = 123.45

        manager = TokenManager()
        yield manager, mock_pricing_instance # Provide manager and mock pricing instance

# --- Tests for TokenManager ---

def test_token_manager_initialization(mock_token_manager):
    """Test TokenManager initialization creates a PricingManager."""
    manager, mock_pricing_instance = mock_token_manager
    assert manager.tokens == []
    assert manager.pricing_manager is not None
    # Check if the mock was used
    assert isinstance(manager.pricing_manager, MagicMock)
    # Check if PricingManager() was called during TokenManager init
    assert manager.pricing_manager == mock_pricing_instance


def test_add_token(mock_token_manager):
    """Test adding tokens to the TokenManager."""
    manager, _ = mock_token_manager
    assert len(manager.tokens) == 0

    manager.add_token(model="gpt-4o", input_tokens=10, output_tokens=20, note="first")
    assert len(manager.tokens) == 1
    assert isinstance(manager.tokens[0], TokenCounter)
    assert manager.tokens[0].model == "gpt-4o"
    assert manager.tokens[0].input_tokens == 10
    assert manager.tokens[0].output_tokens == 20
    assert manager.tokens[0].note == "first"

    manager.add_token(model="gemini-flash", input_tokens=5, output_tokens=15)
    assert len(manager.tokens) == 2
    assert isinstance(manager.tokens[1], TokenCounter)
    assert manager.tokens[1].model == "gemini-flash"
    assert manager.tokens[1].input_tokens == 5
    assert manager.tokens[1].output_tokens == 15
    assert manager.tokens[1].note == ""


def test_calculate_total_cost(mock_token_manager):
    """Test that calculate_total_cost calls the pricing manager correctly."""
    manager, mock_pricing_instance = mock_token_manager

    # Add some tokens
    manager.add_token(model="gpt-4o", input_tokens=10, output_tokens=20)
    manager.add_token(model="gemini-flash", input_tokens=5, output_tokens=15)

    # Call the method under test
    total_cost = manager.calculate_total_cost()

    # Assert that the mock pricing manager's method was called with the list of tokens
    mock_pricing_instance.calculate_cost.assert_called_once_with(manager.tokens)

    # Assert that the returned cost is the one defined in the mock fixture
    assert total_cost == 123.45


def test_calculate_total_cost_no_tokens(mock_token_manager):
    """Test calculate_total_cost when no tokens have been added."""
    manager, mock_pricing_instance = mock_token_manager

    total_cost = manager.calculate_total_cost()

    # Assert that the mock pricing manager's method was called with an empty list
    mock_pricing_instance.calculate_cost.assert_called_once_with([])

    # Assert that the returned cost is the one defined in the mock fixture
    # (The mock always returns 123.45 in this setup, regardless of input)
    assert total_cost == 123.45


# --- Tests for Models.get_model ---

# Mock the actual model instances to avoid real initialization
@patch('utils.models.Models.openai', MagicMock(name="openai_normal"))
@patch('utils.models.Models.openai_hot', MagicMock(name="openai_hot"))
@patch('utils.models.Models.openai_mini', MagicMock(name="openai_mini"))
@patch('utils.models.Models.gemini', MagicMock(name="gemini_normal"))
@patch('utils.models.Models.gemini_hot', MagicMock(name="gemini_hot"))
@patch('utils.models.Models.gemini_mini', MagicMock(name="gemini_mini"))
@patch('utils.models.Models.anthropic', MagicMock(name="anthropic_normal"))
@patch('utils.models.Models.anthropic_hot', MagicMock(name="anthropic_hot"))
@patch('utils.models.Models.anthropic_mini', MagicMock(name="anthropic_mini"))
@patch('utils.models.Models.grok', MagicMock(name="grok_normal"))
@patch('utils.models.Models.grok_hot', MagicMock(name="grok_hot"))
@patch('utils.models.Models.grok_mini', MagicMock(name="grok_mini"))
def test_get_model_valid_providers_and_types():
    """Test Models.get_model with valid provider and type combinations."""
    # Test default type ("normal")
    assert Models.get_model("OPENAI").name == "openai_normal"
    assert Models.get_model("GOOGLE").name == "gemini_normal"
    assert Models.get_model("ANTHROPIC").name == "anthropic_normal"
    assert Models.get_model("XAI").name == "grok_normal"

    # Test "mini" type
    assert Models.get_model("OPENAI", "mini").name == "openai_mini"
    assert Models.get_model("GOOGLE", "mini").name == "gemini_mini"
    assert Models.get_model("ANTHROPIC", "mini").name == "anthropic_mini"
    assert Models.get_model("XAI", "mini").name == "grok_mini"

    # Test "hot" type
    assert Models.get_model("OPENAI", "hot").name == "openai_hot"
    assert Models.get_model("GOOGLE", "hot").name == "gemini_hot"
    assert Models.get_model("ANTHROPIC", "hot").name == "anthropic_hot"
    assert Models.get_model("XAI", "hot").name == "grok_hot"

@patch('utils.models.Models.openai', MagicMock(name="openai_normal")) # Need at least one patch for decorator syntax
def test_get_model_invalid_provider():
    """Test Models.get_model with an invalid provider."""
    assert Models.get_model("INVALID_PROVIDER") is None
    assert Models.get_model("INVALID_PROVIDER", "mini") is None

@patch('utils.models.Models.openai', MagicMock(name="openai_normal"))
@patch('utils.models.Models.openai_mini', MagicMock(name="openai_mini"))
@patch('utils.models.Models.openai_hot', MagicMock(name="openai_hot"))
def test_get_model_invalid_type():
    """Test Models.get_model with an invalid type."""
    assert Models.get_model("OPENAI", "invalid_type") is None
    assert Models.get_model("OPENAI", "") is None # Empty type should also likely fail or return default

# --- Placeholder for future tests ---
# (Keep the existing placeholders)
# TODO: Add tests for weaviate_service.py
# TODO: Add integration tests for the prompt flow
# TODO: Add tests for components/ProductCarousel.py


# --- Fixtures for PricingManager Tests ---

@pytest.fixture
def mock_pricing_manager():
    """Fixture to create a PricingManager instance with a mocked cache manager."""
    with patch('utils.models.PricingCacheManager') as MockCacheManager:
        # Configure the mock cache manager instance that will be created
        mock_cache_instance = MockCacheManager.return_value
        mock_cache_instance.get_current_pricing_data.return_value = {
            "date": "20250424",
            "USD/CZK": 23.0, # Use a simple rate for testing
            "api_costs": {
                "gpt_4o_input": 2.5,
                "gpt_4o_output": 10.0,
                "gpt_4o_mini_input": 0.15,
                "gpt_4o_mini_output": 0.6,
                "claude_3_7_sonnet_latest_input": 3.0,
                "claude_3_7_sonnet_latest_output": 15.0,
                "models/gemini_2_0_flash_input": 0.1,
                "models/gemini_2_0_flash_output": 0.4,
                "unknown_model_input": 1.0, # Add a dummy for testing unknown
                "unknown_model_output": 2.0,
            }
        }
        manager = PricingManager()
        yield manager, mock_cache_instance # Provide both manager and mock cache

# --- Tests for PricingManager ---

def test_pricing_manager_initialization(mock_pricing_manager):
    """Test PricingManager initialization creates a PricingCacheManager."""
    manager, mock_cache_instance = mock_pricing_manager
    # Check if the constructor of PricingCacheManager was called
    assert manager.cache_manager is not None
    # In the fixture, we patched the class, so check if the mock was used
    assert isinstance(manager.cache_manager, MagicMock)


def test_get_cost_key(mock_pricing_manager):
    """Test the _get_cost_key helper method."""
    manager, _ = mock_pricing_manager
    assert manager._get_cost_key("gpt-4o", "Input") == "gpt_4o_input"
    assert manager._get_cost_key("gpt-4o-mini", "Output") == "gpt_4o_mini_output"
    assert manager._get_cost_key("claude-3.7-sonnet-latest", "Input") == "claude_3_7_sonnet_latest_input"
    assert manager._get_cost_key("models/gemini-2.0-flash", "Output") == "models/gemini_2_0_flash_output"


def test_calculate_cost_single_token(mock_pricing_manager):
    """Test calculating cost for a single known token type."""
    manager, mock_cache_instance = mock_pricing_manager
    tokens = [TokenCounter(model="gpt-4o", input_tokens=10000, output_tokens=20000)] # 10k input, 20k output

    # Expected cost in USD:
    # Input: (10000 / 1_000_000) * 2.5 = 0.025
    # Output: (20000 / 1_000_000) * 10.0 = 0.2
    # Total USD = 0.225
    # Total CZK = 0.225 * 23.0 = 5.175
    expected_cost = 5.175

    cost = manager.calculate_cost(tokens)
    assert cost == pytest.approx(expected_cost)
    mock_cache_instance.get_current_pricing_data.assert_called_once()


def test_calculate_cost_multiple_tokens(mock_pricing_manager):
    """Test calculating cost for multiple token types."""
    manager, mock_cache_instance = mock_pricing_manager
    tokens = [
        TokenCounter(model="gpt-4o", input_tokens=10000, output_tokens=20000), # Cost: 5.175 CZK
        TokenCounter(model="gpt-4o-mini", input_tokens=50000, output_tokens=100000), # Cost: ( (50k/1M)*0.15 + (100k/1M)*0.6 ) * 23 = (0.0075 + 0.06) * 23 = 0.0675 * 23 = 1.5525 CZK
        TokenCounter(model="models/gemini-2.0-flash", input_tokens=100000, output_tokens=50000) # Cost: ( (100k/1M)*0.1 + (50k/1M)*0.4 ) * 23 = (0.01 + 0.02) * 23 = 0.03 * 23 = 0.69 CZK
    ]
    expected_total_cost = 5.175 + 1.5525 + 0.69 # 7.4175

    cost = manager.calculate_cost(tokens)
    assert cost == pytest.approx(expected_total_cost)
    mock_cache_instance.get_current_pricing_data.assert_called_once()


def test_calculate_cost_unknown_model(mock_pricing_manager, capsys):
    """Test calculating cost when a model's pricing is not found."""
    manager, mock_cache_instance = mock_pricing_manager
    tokens = [TokenCounter(model="unknown-model", input_tokens=10000, output_tokens=20000)]

    # Uses default prices (3 for input, 15 for output) if key not found
    # Expected cost in USD:
    # Input: (10000 / 1_000_000) * 3 = 0.03
    # Output: (20000 / 1_000_000) * 15 = 0.3
    # Total USD = 0.33
    # Total CZK = 0.33 * 23.0 = 7.59
    expected_cost = 7.59

    cost = manager.calculate_cost(tokens)
    assert cost == pytest.approx(expected_cost)
    captured = capsys.readouterr()
    assert "Unknown input model pricing for unknown-model" in captured.out
    assert "Unknown output model pricing for unknown-model" in captured.out


def test_calculate_cost_empty_list(mock_pricing_manager):
    """Test calculating cost for an empty list of tokens."""
    manager, mock_cache_instance = mock_pricing_manager
    tokens = []
    cost = manager.calculate_cost(tokens)
    assert cost == 0.0
    # Should still fetch pricing data once
    mock_cache_instance.get_current_pricing_data.assert_called_once()


# --- Placeholder for future tests ---
# (Keep the existing placeholders)
# TODO: Add tests for TokenManager (requires mocking PricingManager)
# TODO: Add tests for Models.get_model (might require mocking model initializations)


# --- Fixtures for PricingCacheManager Tests ---

@pytest.fixture
def mock_pricing_cache_manager(tmp_path):
    """Fixture to create a PricingCacheManager instance with a temporary cache directory."""
    # Create a temporary directory for the cache file
    cache_dir = tmp_path / "pricing_cache"
    cache_dir.mkdir()
    cache_file_path = cache_dir / "pricing_cache.json"

    # Patch the class attributes to use the temporary path
    with patch.object(PricingCacheManager, 'output_dir', str(cache_dir)), \
         patch.object(PricingCacheManager, 'file_path', str(cache_file_path)):
        manager = PricingCacheManager()
        # Ensure the manager uses the patched path
        manager.output_dir = str(cache_dir)
        manager.file_path = str(cache_file_path)
        yield manager # Provide the manager instance to the test

# --- Tests for PricingCacheManager ---

@patch('utils.models.requests.get')
@patch('utils.models.datetime')
def test_get_usd_czk_exchange_rate_success(mock_datetime, mock_requests_get, mock_pricing_cache_manager):
    """Test successful retrieval of exchange rate."""
    mock_datetime.today.return_value.strftime.return_value = '20250424'
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'kurzy': {'USD': {'dev_stred': 23.5}}
    }
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    rate = mock_pricing_cache_manager.get_usd_czk_exchange_rate('20250424')
    assert rate == 23.5
    mock_requests_get.assert_called_once_with('https://data.kurzy.cz/json/meny/b[6]den[20250424].json', timeout=5)

@patch('utils.models.requests.get')
def test_get_usd_czk_exchange_rate_timeout(mock_requests_get, mock_pricing_cache_manager, capsys):
    """Test exchange rate retrieval timeout."""
    mock_requests_get.side_effect = requests.exceptions.Timeout
    rate = mock_pricing_cache_manager.get_usd_czk_exchange_rate('20250424')
    assert rate == 23 # Default fallback value
    captured = capsys.readouterr()
    assert "Požadavek na API vypršel pro datum 20250424." in captured.out

@patch('utils.models.requests.get')
def test_get_usd_czk_exchange_rate_connection_error(mock_requests_get, mock_pricing_cache_manager, capsys):
    """Test exchange rate retrieval connection error."""
    mock_requests_get.side_effect = requests.exceptions.ConnectionError
    rate = mock_pricing_cache_manager.get_usd_czk_exchange_rate('20250424')
    assert rate == 23
    captured = capsys.readouterr()
    assert "Nepodařilo se připojit k API pro datum 20250424." in captured.out

@patch('utils.models.requests.get')
def test_get_usd_czk_exchange_rate_http_error(mock_requests_get, mock_pricing_cache_manager, capsys):
    """Test exchange rate retrieval HTTP error."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
    mock_requests_get.return_value = mock_response
    rate = mock_pricing_cache_manager.get_usd_czk_exchange_rate('20250424')
    assert rate == 23
    captured = capsys.readouterr()
    assert "HTTP chyba při získávání dat pro datum 20250424" in captured.out

@patch('utils.models.requests.get')
def test_get_usd_czk_exchange_rate_key_error(mock_requests_get, mock_pricing_cache_manager, capsys):
    """Test exchange rate retrieval key error during JSON processing."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'kurzy': {}} # Missing 'USD' key
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response
    rate = mock_pricing_cache_manager.get_usd_czk_exchange_rate('20250424')
    assert rate == 23
    captured = capsys.readouterr()
    assert "Chyba při zpracování dat z API pro datum 20250424" in captured.out

def test_read_from_file_exists(mock_pricing_cache_manager):
    """Test reading from an existing cache file."""
    expected_data = {"date": "20250424", "USD/CZK": 23.5}
    # Use the patched file_path from the fixture
    with open(mock_pricing_cache_manager.file_path, 'w', encoding='utf-8') as f:
        json.dump(expected_data, f)

    data = mock_pricing_cache_manager.read_from_file(mock_pricing_cache_manager.file_path)
    assert data == expected_data

def test_read_from_file_not_exists(mock_pricing_cache_manager):
    """Test reading when the cache file does not exist."""
    # Ensure file does not exist (though tmp_path should handle this)
    if os.path.exists(mock_pricing_cache_manager.file_path):
        os.remove(mock_pricing_cache_manager.file_path)

    data = mock_pricing_cache_manager.read_from_file(mock_pricing_cache_manager.file_path)
    assert data is None

def test_get_api_costs(mock_pricing_cache_manager):
    """Test that get_api_costs returns the expected structure."""
    costs = mock_pricing_cache_manager.get_api_costs()
    assert isinstance(costs, dict)
    assert "gpt_4o_input" in costs
    assert "gpt_4o_output" in costs
    # Add more checks if specific keys/values are critical

def test_get_today_date_formatted(mock_pricing_cache_manager):
    """Test the date formatting function."""
    # We can't easily mock datetime directly here without affecting other tests
    # So we just check the format
    date_str = mock_pricing_cache_manager.get_today_date_formatted()
    assert isinstance(date_str, str)
    assert len(date_str) == 8
    try:
        datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        pytest.fail("Date format is incorrect")

@patch.object(PricingCacheManager, 'read_from_file')
@patch.object(PricingCacheManager, 'update_cached_data')
@patch.object(PricingCacheManager, 'get_today_date_formatted')
def test_get_current_pricing_data_cache_hit(mock_get_date, mock_update_data, mock_read_file, mock_pricing_cache_manager, capsys):
    """Test get_current_pricing_data when cache is valid."""
    today = '20250424'
    mock_get_date.return_value = today
    cached_data = {"date": today, "USD/CZK": 23.5, "api_costs": {"gpt_4o_input": 2.5}}
    mock_read_file.return_value = cached_data

    data = mock_pricing_cache_manager.get_current_pricing_data()

    assert data == cached_data
    mock_read_file.assert_called_once_with(mock_pricing_cache_manager.file_path)
    mock_update_data.assert_not_called()
    captured = capsys.readouterr()
    assert "Cashed data, načítáme ze souboru" in captured.out

@patch.object(PricingCacheManager, 'read_from_file')
@patch.object(PricingCacheManager, 'update_cached_data')
@patch.object(PricingCacheManager, 'get_today_date_formatted')
def test_get_current_pricing_data_cache_miss_date(mock_get_date, mock_update_data, mock_read_file, mock_pricing_cache_manager, capsys):
    """Test get_current_pricing_data when cache is outdated."""
    today = '20250424'
    yesterday = '20250423'
    mock_get_date.return_value = today
    cached_data = {"date": yesterday, "USD/CZK": 23.0, "api_costs": {}}
    mock_read_file.return_value = cached_data
    updated_data = {"date": today, "USD/CZK": 23.5, "api_costs": {"gpt_4o_input": 2.5}}
    mock_update_data.return_value = updated_data

    data = mock_pricing_cache_manager.get_current_pricing_data()

    assert data == updated_data
    mock_read_file.assert_called_once_with(mock_pricing_cache_manager.file_path)
    mock_update_data.assert_called_once_with(today)
    captured = capsys.readouterr()
    assert "Aktualizace cached dat" in captured.out

@patch.object(PricingCacheManager, 'read_from_file')
@patch.object(PricingCacheManager, 'update_cached_data')
@patch.object(PricingCacheManager, 'get_today_date_formatted')
def test_get_current_pricing_data_cache_miss_no_file(mock_get_date, mock_update_data, mock_read_file, mock_pricing_cache_manager, capsys):
    """Test get_current_pricing_data when cache file doesn't exist."""
    today = '20250424'
    mock_get_date.return_value = today
    mock_read_file.return_value = None # Simulate file not found
    updated_data = {"date": today, "USD/CZK": 23.5, "api_costs": {"gpt_4o_input": 2.5}}
    mock_update_data.return_value = updated_data

    data = mock_pricing_cache_manager.get_current_pricing_data()

    assert data == updated_data
    mock_read_file.assert_called_once_with(mock_pricing_cache_manager.file_path)
    mock_update_data.assert_called_once_with(today)
    captured = capsys.readouterr()
    assert "Žádné cached data, vytvářím..." in captured.out


@patch('utils.models.json.dump')
@patch('builtins.open', new_callable=MagicMock)
@patch.object(PricingCacheManager, 'get_usd_czk_exchange_rate')
@patch.object(PricingCacheManager, 'get_api_costs')
def test_update_cached_data_success(mock_get_costs, mock_get_rate, mock_open, mock_json_dump, mock_pricing_cache_manager):
    """Test successful update of cached data."""
    today = '20250424'
    mock_get_rate.return_value = 23.5
    mock_api_costs = {"gpt_4o_input": 2.5}
    mock_get_costs.return_value = mock_api_costs
    expected_data = {
        "date": today,
        "USD/CZK": 23.5,
        "api_costs": mock_api_costs
    }

    # Mock the file handle returned by open
    mock_file_handle = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file_handle

    result_data = mock_pricing_cache_manager.update_cached_data(today)

    assert result_data == expected_data
    mock_get_rate.assert_called_once_with(today)
    mock_get_costs.assert_called_once()
    # Use the patched file_path from the fixture
    mock_open.assert_called_once_with(mock_pricing_cache_manager.file_path, 'w', encoding='utf-8')
    mock_json_dump.assert_called_once_with(expected_data, mock_file_handle, indent=4)

@patch.object(PricingCacheManager, 'get_usd_czk_exchange_rate')
def test_update_cached_data_request_exception(mock_get_rate, mock_pricing_cache_manager, capsys):
    """Test update_cached_data when fetching exchange rate fails."""
    today = '20250424'
    mock_get_rate.side_effect = requests.exceptions.RequestException("API Error")

    result_data = mock_pricing_cache_manager.update_cached_data(today)

    # Should return an empty dict on failure
    assert result_data == {}
    captured = capsys.readouterr()
    assert "Error fetching data: API Error" in captured.out

# --- Placeholder for future tests ---
# (Keep the existing placeholders)
# TODO: Add tests for PricingManager (requires mocking PricingCacheManager or providing fixed data)
# TODO: Add tests for TokenManager (requires mocking PricingManager)
# TODO: Add tests for Models.get_model (might require mocking model initializations)
