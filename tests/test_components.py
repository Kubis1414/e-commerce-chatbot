# tests/test_components.py
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from components.ProductCarousel import product_carousel

@pytest.fixture
def sample_products():
    """Sample product data for testing the carousel."""
    return [
        {
            "name": "iPhone 15 Pro Max 256GB",
            "url": "https://eshop.cz/mobily/iphone-15-pro-max-256gb",
            "image_url": "https://example.com/iphone15promax.jpg",
            "description": "iPhone 15 Pro Max je nejnovější model s pamětí 256GB a procesorem A17 Pro.",
            "price": 38990.0
        },
        {
            "name": "iPhone 15 Pro 128GB",
            "url": "https://eshop.cz/mobily/iphone-15-pro-128gb",
            "image_url": "https://example.com/iphone15pro.jpg",
            "description": "iPhone 15 Pro je vlajkový model Apple s pamětí 128GB a procesorem A17 Pro.",
            "price": 33990.0
        }
    ]

@pytest.fixture
def incomplete_products():
    """Sample product data with missing fields."""
    return [
        {
            "name": "iPhone 15 Pro Max 256GB",
            # Missing URL
            "image_url": "",  # Empty image URL
            "description": "iPhone 15 Pro Max je nejnovější model s pamětí 256GB a procesorem A17 Pro.",
            # Missing price
        },
        {
            # Missing name
            "url": "https://eshop.cz/mobily/iphone15pro",
            # Missing image_url entirely
            "description": None,  # None description
            "price": 0  # Zero price
        }
    ]

# Mock Streamlit dependency for testing
@pytest.fixture
def mock_streamlit():
    """Mock all Streamlit functions used in the component."""
    with patch('components.ProductCarousel.st') as mock_st:
        # Setup column mocking
        mock_columns = [MagicMock() for _ in range(4)]  # Create mocks for up to 4 columns
        mock_st.columns.return_value = mock_columns
        
        # For each column, configure context manager behavior
        for col in mock_columns:
            # Make the context manager return the mock itself
            col.__enter__.return_value = col
            col.__exit__.return_value = None
        
        yield mock_st

def test_product_carousel_with_valid_products(mock_streamlit, sample_products):
    """Test product_carousel with valid product data."""
    # Call the function
    product_carousel(sample_products)
    
    # Verify Streamlit calls
    mock_streamlit.markdown.assert_called()  # CSS style is applied
    mock_streamlit.columns.assert_called_once_with(2)  # Should create 2 columns for 2 products
    
    # Verify product rendering (checking for product names in HTML)
    html_calls = [call_args[0][0] for call_args in mock_streamlit.markdown.call_args_list]
    html_content = ''.join(str(h) for h in html_calls if isinstance(h, str))
    
    # Check if product information is in the HTML
    assert "iPhone 15 Pro Max 256GB" in html_content
    assert "iPhone 15 Pro 128GB" in html_content
    assert "38 990 Kč" in html_content  # Formatted price
    assert "33 990 Kč" in html_content  # Formatted price
    assert "https://example.com/iphone15promax.jpg" in html_content
    assert "https://eshop.cz/mobily/iphone-15-pro-max-256gb" in html_content

def test_product_carousel_with_no_products(mock_streamlit):
    """Test product_carousel with an empty product list."""
    product_carousel([])
    
    # Should show a message about no products
    mock_streamlit.write.assert_called_once_with("Žádné doporučené produkty k zobrazení.")
    # Should not create any columns
    mock_streamlit.columns.assert_not_called()

def test_product_carousel_with_incomplete_data(mock_streamlit, incomplete_products):
    """Test product_carousel with incomplete product data."""
    product_carousel(incomplete_products)
    
    # Verify column creation
    mock_streamlit.columns.assert_called_once_with(2)
    
    # Verify rendered HTML
    html_calls = [call_args[0][0] for call_args in mock_streamlit.markdown.call_args_list]
    html_content = ''.join(str(h) for h in html_calls if isinstance(h, str))
    
    # Check if fallback values are used
    assert "Neznámý produkt" in html_content  # Default name
    assert "Cena neuvedena" in html_content  # Default price text
    assert "obrázek+není+k+dispozici" in html_content.lower()  # Placeholder image
    assert "<div class=\"product-card-link\">" in html_content  # Non-link container when URL missing

def test_long_description_truncation(mock_streamlit):
    """Test that long descriptions are properly truncated."""
    long_description = "This is a very long description that exceeds the 70 character limit and should be truncated in the display."
    product_with_long_desc = [{
        "name": "Test Product",
        "description": long_description,
        "price": 1000
    }]
    
    product_carousel(product_with_long_desc)
    
    html_calls = [call_args[0][0] for call_args in mock_streamlit.markdown.call_args_list]
    html_content = ''.join(str(h) for h in html_calls if isinstance(h, str))
    
    # Check truncation
    # Full description shouldn't be directly visible in main display text
    assert long_description not in html_content or (
        # It's okay to be in title attribute for tooltips
        "title=\"" + long_description + "\"" in html_content and 
        long_description + "..." not in html_content.replace("title=\"" + long_description + "\"", "")
    )
    truncated = long_description[:67] + "..."  # 67 chars + 3 dots = 70
    assert truncated in html_content
    assert f'title="{long_description}"' in html_content  # Full text as tooltip

def test_price_formatting(mock_streamlit):
    """Test that prices are properly formatted."""
    products_with_prices = [
        {"name": "Product 1", "price": 1000},
        {"name": "Product 2", "price": 1000.50},  # Should round to 1 001
        {"name": "Product 3", "price": 1000000},  # Should use space as thousands separator
    ]
    
    product_carousel(products_with_prices)
    
    html_calls = [call_args[0][0] for call_args in mock_streamlit.markdown.call_args_list]
    html_content = ''.join(str(h) for h in html_calls if isinstance(h, str))
    
    assert "1 000 Kč" in html_content
    # Check only for the amount
    assert "1 000 kč" in html_content.lower()  # Test basic price format
    assert "1 000 000 Kč" in html_content  # Testing thousands separator
