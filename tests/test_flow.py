import pytest
from flow.generate_search_queries import generate_search_queries
from flow.get_answer import get_answer
from flow.get_customer_info import get_customer_info
from flow.get_documents_from_vector_db import get_documents_from_vector_db

@pytest.fixture
def sample_context():
    return {
        "page_title": "Domů - E-shop s elektronikou",
        "current_url": "https://eshop.cz/",
        "language": "CS"
    }

@pytest.fixture
def sample_customer():
    return {
        "customer_id": "CUS765894089"
    }

@pytest.fixture
def sample_chat_history():
    return [
        {"role": "user", "content": "Jaké máte mobilní telefony?"},
        {"role": "assistant", "content": "Máme širokou nabídku mobilních telefonů..."}
    ]

def test_generate_search_queries():
    """Test generování vyhledávacích dotazů"""
    customer_input = "Jaké máte iPhony?"
    queries = generate_search_queries(customer_input)
    assert isinstance(queries, list)
    assert len(queries) > 0
    for query in queries:
        assert isinstance(query, str)
        assert len(query) > 0

def test_get_answer(sample_context, sample_customer, sample_chat_history):
    """Test generování odpovědi"""
    customer_input = "Jaké máte iPhony?"
    response = get_answer(
        customer_input=customer_input,
        context=sample_context,
        customer=sample_customer,
        chat_history=sample_chat_history,
        llm_provider="GOOGLE"
    )
    assert isinstance(response, dict)
    assert "answer" in response
    assert isinstance(response["answer"], str)
    assert "recommended_products" in response

def test_get_customer_info(sample_customer):
    """Test získávání informací o zákazníkovi"""
    customer_info = get_customer_info(sample_customer["customer_id"])
    assert isinstance(customer_info, dict)
    assert "customer_id" in customer_info
    assert customer_info["customer_id"] == sample_customer["customer_id"]

def test_get_documents_from_vector_db():
    """Test získávání dokumentů z vektorové databáze"""
    query = "iPhone 15 Pro Max"
    docs = get_documents_from_vector_db(query)
    assert isinstance(docs, list)
    for doc in docs:
        assert isinstance(doc, dict)
        assert "content" in doc 