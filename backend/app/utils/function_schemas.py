"""
Function schemas for LLM tool/function calling
"""

CURRENCY_CONVERSION_SCHEMA = {
    "name": "convert_currency",
    "description": "Convert amount from one currency to another using real-time exchange rates",
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {
                "type": "number",
                "description": "Amount to convert (must be positive)"
            },
            "from_currency": {
                "type": "string",
                "description": "Source currency code (3-letter ISO code, e.g., USD, EUR, GBP)",
                "pattern": "^[A-Z]{3}$"
            },
            "to_currency": {
                "type": "string", 
                "description": "Target currency code (3-letter ISO code, e.g., USD, EUR, GBP)",
                "pattern": "^[A-Z]{3}$"
            }
        },
        "required": ["amount", "from_currency", "to_currency"]
    }
}

CURRENCY_LIST_SCHEMA = {
    "name": "get_supported_currencies",
    "description": "Get list of all supported currencies",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}

HISTORICAL_RATE_SCHEMA = {
    "name": "get_historical_rate",
    "description": "Get historical exchange rate for a specific date",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "from_currency": {
                "type": "string",
                "description": "Source currency code",
                "pattern": "^[A-Z]{3}$"
            },
            "to_currency": {
                "type": "string",
                "description": "Target currency code", 
                "pattern": "^[A-Z]{3}$"
            }
        },
        "required": ["date", "from_currency", "to_currency"]
    }
}

# All available functions for the LLM
AVAILABLE_FUNCTIONS = [
    CURRENCY_CONVERSION_SCHEMA,
    CURRENCY_LIST_SCHEMA,
    HISTORICAL_RATE_SCHEMA
]

# System prompt for the currency converter agent
SYSTEM_PROMPT = """You are a helpful currency conversion assistant. You can:

1. Convert currencies using real-time exchange rates
2. Handle multiple currency conversions in a single request
3. Provide information about supported currencies
4. Get historical exchange rates for specific dates

Always provide clear, accurate information about currency conversions. When multiple conversions are requested, process all of them and present the results clearly.

If a user asks about something unrelated to currency conversion, politely redirect them to currency-related topics.

Format your responses in a clear, user-friendly manner with:
- The original amount and currency
- The converted amount and target currency
- The exchange rate used
- The date of the exchange rate

For multiple conversions, present each conversion in a separate, clearly marked section."""