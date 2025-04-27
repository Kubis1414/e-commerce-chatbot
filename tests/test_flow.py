from unittest.mock import patch, MagicMock
import pytest
from promptflow.client import PFClient
from flow.generate_search_queries import generate_search_queries
from flow.get_answer import get_answer
from flow.get_customer_info import get_customer_info
from flow.get_documents_from_vector_db import get_documents_from_vector_db
from utils.models import TokenManager
from utils.weaviate_service import Document, SearchQuery

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

@pytest.fixture
def sample_search_queries():
    """Sample search queries for vector DB lookup."""
    return [
        SearchQuery(query="iPhone 15", min_price=20000, max_price=40000),
        SearchQuery(query="iPhone Pro Max", product_code="APP-IP15PM")
    ]

@pytest.fixture
def sample_document_objects():
    """Sample document objects returned from Weaviate."""
    return [
        Document(
            name="iPhone 15 Pro Max 256GB",
            content="iPhone 15 Pro Max je nejnovější model s pamětí 256GB a procesoremA17 Pro.",
            url="https://eshop.cz/mobily/iphone-15-pro-max-256gb",
            product_code="APP-IP15PM-256",
            price=38990.0
        ),
        Document(
            name="iPhone 15 Pro 128GB",
            content="iPhone 15 Pro je vlajkový model Apple s pamětí 128GB a procesoremA17 Pro.",
            url="https://eshop.cz/mobily/iphone-15-pro-128gb",
            product_code="APP-IP15P-128",
            price=33990.0
        ),
        # Duplicate content to test deduplication
        Document(
            name="iPhone 15 Pro Max 256GB (duplikát)",
            content="iPhone 15 Pro Max je nejnovější model s pamětí 256GB a procesoremA17 Pro.",
            url="https://eshop.cz/mobily/iphone-15-pro-max-256gb-alt",
            product_code="APP-IP15PM-256-ALT",
            price=38990.0
        )
    ]

def test_generate_search_queries(sample_chat_history, sample_context):
    """Test generování vyhledávacích dotazů"""
    customer_input = "Jaké máte iPhony?"
    output = generate_search_queries(
        customer_input=customer_input,
        chat_history=sample_chat_history,
        context=sample_context,
        llm_provider="OPENAI"
    )
    queries = output.search_queries
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
        documents=sample_documents,
        search_queries=[], 
        token_manager=TokenManager()
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

@patch('flow.get_documents_from_vector_db.WeaviateService')
def test_get_documents_from_vector_db(mock_weaviate_service, sample_search_queries, sample_document_objects):
    """Test získávání dokumentů z vektorové databáze včetně deduplikace."""
    # Setup the mock WeaviateService 
    mock_instance = mock_weaviate_service.return_value
    
    # Configure the search_products method to return different documents for each query
    mock_instance.search_products.side_effect = [
        [sample_document_objects[0], sample_document_objects[2]],  # First query - includes duplicate content
        [sample_document_objects[1]]  # Second query
    ]
    
    # Call the function under test
    documents = get_documents_from_vector_db(search_queries=sample_search_queries)
    
    # Verify the results
    assert len(documents) == 2  # Should be 2 after deduplication (not 3)
    assert documents[0].name == "iPhone 15 Pro Max 256GB"
    assert documents[1].name == "iPhone 15 Pro 128GB"
    
    # Verify WeaviateService was used correctly
    mock_weaviate_service.assert_called_once()
    assert mock_instance.search_products.call_count == 2  # Called for each query
    mock_instance.close.assert_called_once()  # Service should be closed

@patch('flow.get_documents_from_vector_db.WeaviateService')
@patch('flow.generate_search_queries.Models')
def test_flow_integration(mock_models_class, mock_weaviate_service, sample_context, sample_customer, sample_chat_history, sample_document_objects):
    """Integration test for the full prompt flow"""
    # 1. Mock the LLM model for generate_search_queries
    mock_model = MagicMock()
    mock_model.invoke.return_value = "1. iPhone 15 Pro Max \n2. iPhone 15 comparison"
    mock_models_class.get_model.return_value = mock_model
    
    # 2. Setup the WeaviateService mock for get_documents_from_vector_db
    mock_weaviate_instance = mock_weaviate_service.return_value
    mock_weaviate_instance.search_products.return_value = sample_document_objects[:2]  # Return two documents
    
    # Start with a simple flow test - run the nodes manually in sequence
    
    # Step 1: Get customer info
    customer_info = get_customer_info(sample_customer)
    assert isinstance(customer_info, dict)
    assert customer_info["customer_id"] == sample_customer["customer_id"]
    
    # Step 2: Generate search queries
    customer_input = "Kolik stojí iPhone 15 Pro Max?"
    with patch('flow.generate_search_queries._extract_token_counts', return_value=(100, 50)):
        query_output = generate_search_queries(
            customer_input=customer_input,
            chat_history=sample_chat_history,
            context=sample_context,
            llm_provider="OPENAI"
        )
    
    # Verify search queries were generated
    assert hasattr(query_output, "search_queries")
    assert isinstance(query_output.search_queries, list)
    
    # Step 3: Get documents from vector DB
    documents = get_documents_from_vector_db(search_queries=query_output.search_queries)
    
    # Verify documents were retrieved
    assert isinstance(documents, list)
    assert len(documents) > 0
    assert hasattr(documents[0], "name")
    assert hasattr(documents[0], "content")
    
    # Step 4: Generate final answer
    with patch('flow.get_answer._extract_token_counts', return_value=(200, 100)):
        answer_output = get_answer(
            customer_input=customer_input,
            context=sample_context,
            customer=customer_info,
            chat_history=sample_chat_history,
            llm_provider="OPENAI",
            documents=documents,
            search_queries=query_output.search_queries,
            token_manager=query_output.token_manager
        )
    
    # Verify the answer output structure
    assert isinstance(answer_output, dict)
    assert "response" in answer_output
    assert "answer" in answer_output["response"]
    assert isinstance(answer_output["response"]["answer"], str)
    assert "cost" in answer_output
    assert isinstance(answer_output["cost"], (float, int))
    
    # Verify the expected service calls
    mock_models_class.get_model.assert_called()
    mock_weaviate_service.assert_called_once()
    mock_weaviate_instance.search_products.assert_called()
    mock_weaviate_instance.close.assert_called_once()
