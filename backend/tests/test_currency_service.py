# backend/tests/test_currency_service.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.currency_service import CurrencyService

@pytest.fixture
def currency_service():
    return CurrencyService()

@pytest.mark.asyncio
async def test_convert_currency_success(currency_service):
    """Test successful currency conversion"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {
            "rates": {"EUR": 85.0},
            "date": "2024-01-15"
        }
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await currency_service.convert_currency(100, "USD", "EUR")
        
        assert result["amount"] == 100
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "EUR"
        assert result["converted_amount"] == 85.0

@pytest.mark.asyncio
async def test_convert_same_currency(currency_service):
    """Test converting same currency returns 1:1 rate"""
    result = await currency_service.convert_currency(100, "USD", "USD")
    
    assert result["converted_amount"] == 100
    assert result["exchange_rate"] == 1.0

# backend/tests/test_llm_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.llm_service import LLMService

@pytest.fixture
def llm_service():
    return LLMService()

def test_extract_conversions(llm_service):
    """Test regex extraction of currency conversions"""
    test_cases = [
        ("Convert 100 USD to EUR", [{"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}]),
        ("100 USD to EUR and 200 GBP to JPY", [
            {"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"},
            {"amount": 200.0, "from_currency": "GBP", "to_currency": "JPY"}
        ]),
        ("What is the weather?", [])
    ]
    
    for query, expected in test_cases:
        result = llm_service._extract_conversions(query)
        assert result == expected

@pytest.mark.asyncio
async def test_process_query_with_direct_conversion(llm_service):
    """Test processing query with direct conversion detection"""
    with patch.object(llm_service.currency_service, 'convert_multiple_currencies', new_callable=AsyncMock) as mock_convert:
        mock_convert.return_value = [{
            "amount": 100.0,
            "from_currency": "USD", 
            "to_currency": "EUR",
            "converted_amount": 85.0,
            "exchange_rate": 0.85,
            "date": "2024-01-15"
        }]
        
        result = await llm_service.process_query("Convert 100 USD to EUR")
        
        mock_convert.assert_called_once()
        assert "100 USD" in result
        assert "85.0 EUR" in result

# backend/tests/test_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat_completion_endpoint():
    """Test chat completion endpoint"""
    request_data = {
        "message": "Convert 100 USD to EUR",
        "session_id": "test-session"
    }
    
    response = client.post("/api/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "session_id" in data

def test_invalid_chat_request():
    """Test invalid chat request"""
    request_data = {
        "message": "",  # Empty message should fail validation
        "session_id": "test-session"
    }
    
    response = client.post("/api/v1/chat/completions", json=request_data)
    assert response.status_code == 422  # Validation error