import pytest
from promptflow.client import PFClient
from flow.generate_search_queries import generate_search_queries
from flow.get_answer import get_answer
from flow.get_customer_info import get_customer_info

pf_client = PFClient()

@pytest.fixture
def sample_context():
    return {
        'page_title': 'Mobilní telefon iPhone 15 Pro Max',
        'current_url': 'https://eshop.cz/mobily/iphone-15-pro-max',
        'language': 'CS'
    }

@pytest.fixture
def sample_customer():
    return {
        "customer_id": "CUS788902345",
        "name": "Eva Černá",
        "vokative": "Evo",
        "email": "eva.cerna@email.cz",
        "favorite_brands": ["Apple", "Lego"]
    }

@pytest.fixture
def sample_chat_history():
    return [
        {
            'customer_input': 'ahoj',
            'assistant_answer': 'Ahoj! Jak ti mohu dnes pomoci?'
        }
    ]

@pytest.fixture
def sample_documents():
    return [
        {
            "content": "iPhone 15 Pro Max je nejnovější model...",
            "metadata": {"type": "product", "id": "123"}
        }
    ]

def test_generate_search_queries(sample_chat_history, sample_context):
    """Test generování vyhledávacích dotazů"""
    customer_input = "Jaké máte iPhony?"
    queries = generate_search_queries(
        customer_input=customer_input,
        chat_history=sample_chat_history,
        context=sample_context,
        llm_provider="GOOGLE"
    )
    assert isinstance(queries, list)
    assert len(queries) > 0
    

def test_get_answer(sample_context, sample_customer, sample_chat_history, sample_documents):
    """Test generování odpovědi"""
    customer_input = "Jaké máte iPhony?"
    output_data = get_answer(
        customer_input=customer_input,
        context=sample_context,
        customer=sample_customer,
        chat_history=sample_chat_history,
        llm_provider="GOOGLE",
        documents=sample_documents
    )
    assert isinstance(output_data, dict)
    assert "response" in output_data
    assert isinstance(output_data["response"], dict)
    assert "answer" in output_data["response"]
    assert isinstance(output_data["response"]["answer"], str)
    assert "recommended_products" in output_data["response"]
    assert isinstance(output_data["response"]["recommended_products"], list)

def test_get_customer_info(sample_customer):
    """Test získávání informací o zákazníkovi"""
    customer_info = get_customer_info(sample_customer)
    assert isinstance(customer_info, dict)
    assert "customer_id" in customer_info
    assert customer_info["customer_id"] == sample_customer["customer_id"]
