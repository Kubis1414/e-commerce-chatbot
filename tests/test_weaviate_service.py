# tests/test_weaviate_service.py
import pytest
from unittest.mock import MagicMock, patch
from utils.weaviate_service import Document, SearchQuery, WeaviateService

# === Tests for Document and SearchQuery models ===
def test_document_creation():
    """Test creating a Document with various fields."""
    # Full document
    doc = Document(
        name="Test Product",
        content="Product description",
        url="http://example.com/product",
        product_code="TP123",
        price=99.99
    )
    assert doc.name == "Test Product"
    assert doc.content == "Product description"
    assert doc.url == "http://example.com/product"
    assert doc.product_code == "TP123"
    assert doc.price == 99.99

    # Document with minimal fields
    doc_minimal = Document(name="Minimal Product")
    assert doc_minimal.name == "Minimal Product"
    assert doc_minimal.content is None
    assert doc_minimal.price is None

def test_search_query_validation():
    """Test SearchQuery creation and validation."""
    # Basic query
    query = SearchQuery(query="iPhone")
    assert query.query == "iPhone"
    assert query.min_price is None
    assert query.max_price is None

    # Query with price range
    query_with_price = SearchQuery(query="iPhone", min_price=500, max_price=1000)
    assert query_with_price.query == "iPhone"
    assert query_with_price.min_price == 500
    assert query_with_price.max_price == 1000

    # Invalid price range should raise ValueError
    with pytest.raises(ValueError):
        SearchQuery(query="iPhone", min_price=1000, max_price=500)

# === Tests for WeaviateService ===

@patch('utils.weaviate_service.weaviate')
def test_weaviate_service_document_extraction(mock_weaviate):
    """Test extracting Document objects from Weaviate results."""
    # Create a mock WeaviateService without connecting to actual Weaviate
    with patch.object(WeaviateService, '__init__', return_value=None):
        service = WeaviateService()
        service.client = MagicMock()
        service.collection_name = "Apple_Products"
        
        # Mock Weaviate objects with properties
        mock_obj1 = MagicMock()
        mock_obj1.properties = {
            "name": "iPhone 15 Pro", 
            "price": 999.0,
            "product_code": "IP15P", 
            "url": "http://example.com/iphone15pro",
            "content": "iPhone 15 Pro features the A17 Pro chip..."
        }
        
        mock_obj2 = MagicMock()
        mock_obj2.properties = {
            "name": "MacBook Air", 
            "price": 1199.0,
            "content": "Thin and light laptop..."
        }
        
        # Test extraction of multiple objects
        results = [mock_obj1, mock_obj2]
        documents = service.extract_and_print_properties(results)
        
        assert len(documents) == 2
        assert isinstance(documents[0], Document)
        assert documents[0].name == "iPhone 15 Pro"
        assert documents[0].price == 999.0
        assert documents[1].name == "MacBook Air"
        
        # Test handling of invalid properties
        mock_obj_invalid = MagicMock()
        mock_obj_invalid.properties = "not a dict"
        results_with_invalid = [mock_obj1, mock_obj_invalid]
        
        documents = service.extract_and_print_properties(results_with_invalid)
        assert len(documents) == 1  # Only the valid object should be extracted
        
        # Test empty input
        empty_results = []
        documents = service.extract_and_print_properties(empty_results)
        assert len(documents) == 0

@patch('utils.weaviate_service.weaviate')
def test_weaviate_service_search_products(mock_weaviate):
    """Test searching for products with various parameters."""
    # Create a mock WeaviateService without connecting to actual Weaviate
    with patch.object(WeaviateService, '__init__', return_value=None):
        service = WeaviateService()
        service.client = MagicMock()
        service.client.is_connected.return_value = True
        service.collection_name = "Apple_Products"
        
        # Setup mock collection and query
        mock_collection = MagicMock()
        mock_query = MagicMock()
        mock_response = MagicMock()
        
        # Mock the response objects
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "iPhone 15", 
            "price": 799.0,
            "product_code": "IP15"
        }
        mock_response.objects = [mock_obj]
        
        # Setup the chain of mocks
        mock_query.near_text.return_value = mock_response
        mock_collection.query = mock_query
        service.client.collections.get.return_value = mock_collection
        
        # Mock the extract_and_print_properties method to return documents directly
        with patch.object(service, 'extract_and_print_properties', return_value=[Document(**mock_obj.properties)]):
            # Test basic search
            search_params = SearchQuery(query="iPhone")
            results = service.search_products(search_params=search_params)
            
            assert len(results) == 1
            assert results[0].name == "iPhone 15"
            assert results[0].price == 799.0
            
            # Verify near_text was called correctly
            mock_query.near_text.assert_called()
            args, kwargs = mock_query.near_text.call_args
            assert kwargs['query'] == "iPhone"
            assert kwargs['limit'] == 5  # Default limit
            
            # Test search with price filters
            search_params = SearchQuery(query="iPhone", min_price=700, max_price=900)
            service.search_products(search_params=search_params)
            
            # Verify filters were created correctly
            args, kwargs = mock_query.near_text.call_args
            assert kwargs['filters'] is not None
            
            # Test invalid client connection
            service.client.is_connected.return_value = False
            results = service.search_products(search_params=search_params)
            assert results == []  # Should return empty list when not connected

@patch('utils.weaviate_service.weaviate')
def test_weaviate_service_client_lifecycle(mock_weaviate):
    """Test client connection and closing."""
    # Test closing a connected client
    with patch.object(WeaviateService, '__init__', return_value=None):
        service = WeaviateService()
        mock_client = MagicMock()
        mock_client.is_connected.return_value = True
        service.client = mock_client
        
        service.close()
        mock_client.close.assert_called_once()
        assert service.client is None
        
        # Test closing when client is None
        service.client = None
        service.close()  # Should not raise any errors
