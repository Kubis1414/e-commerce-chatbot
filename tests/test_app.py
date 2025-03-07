import pytest
import streamlit as st
from app import PAGE_DATA, CUSTOMER_IDS, LANGUAGES, LLM_PROVIDERS

def test_page_data_structure():
    """Test struktury PAGE_DATA"""
    for page in PAGE_DATA:
        assert "title" in page
        assert "url" in page
        assert isinstance(page["title"], str)
        assert isinstance(page["url"], str)
        assert page["url"].startswith("https://")

def test_customer_ids():
    """Test seznamu zákazníků"""
    assert "anonymous" in CUSTOMER_IDS
    assert len(CUSTOMER_IDS) > 1
    for customer_id in CUSTOMER_IDS:
        assert isinstance(customer_id, str)
        if customer_id != "anonymous":
            assert customer_id.startswith("CUS")
            assert len(customer_id) == 12

def test_languages():
    """Test dostupných jazyků"""
    assert "CS" in LANGUAGES
    assert "EN" in LANGUAGES
    assert "SK" in LANGUAGES
    assert "DE" in LANGUAGES
    for code, language in LANGUAGES.items():
        assert isinstance(code, str)
        assert isinstance(language, str)
        assert len(code) == 2

def test_llm_providers():
    """Test dostupných LLM poskytovatelů"""
    assert "GOOGLE" in LLM_PROVIDERS
    assert "OPENAI" in LLM_PROVIDERS
    assert "ANTHROPIC" in LLM_PROVIDERS
    for provider, name in LLM_PROVIDERS.items():
        assert isinstance(provider, str)
        assert isinstance(name, str) 