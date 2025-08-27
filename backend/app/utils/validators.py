import re
from typing import Optional, Tuple, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class CurrencyValidator:
    # Common currency codes for validation
    COMMON_CURRENCIES = {
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
        'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON', 'BGN',
        'HRK', 'RUB', 'TRY', 'CNY', 'HKD', 'SGD', 'KRW', 'INR',
        'BRL', 'MXN', 'ZAR', 'ILS', 'THB', 'MYR', 'IDR', 'PHP'
    }
    
    @staticmethod
    def validate_currency_code(currency_code: str) -> str:
        """
        Validate and normalize currency code
        """
        if not currency_code:
            raise ValidationError("Currency code cannot be empty")
        
        currency_code = currency_code.strip().upper()
        
        if len(currency_code) != 3:
            raise ValidationError(f"Currency code must be 3 characters long: {currency_code}")
        
        if not currency_code.isalpha():
            raise ValidationError(f"Currency code must contain only letters: {currency_code}")
        
        # Note: We don't validate against COMMON_CURRENCIES here as Frankfurter supports more
        # currencies than our common list, and we want to let the API validate supported currencies
        
        return currency_code
    
    @staticmethod
    def validate_amount(amount: float) -> float:
        """
        Validate currency amount
        """
        if amount is None:
            raise ValidationError("Amount cannot be None")
        
        if not isinstance(amount, (int, float)):
            raise ValidationError(f"Amount must be a number: {type(amount)}")
        
        if amount <= 0:
            raise ValidationError(f"Amount must be positive: {amount}")
        
        if amount > 1e12:  # 1 trillion limit
            raise ValidationError(f"Amount is too large: {amount}")
        
        return float(amount)
    
    @staticmethod
    def validate_conversion_request(amount: float, from_currency: str, to_currency: str) -> Tuple[float, str, str]:
        """
        Validate complete conversion request
        """
        validated_amount = CurrencyValidator.validate_amount(amount)
        validated_from = CurrencyValidator.validate_currency_code(from_currency)
        validated_to = CurrencyValidator.validate_currency_code(to_currency)
        
        return validated_amount, validated_from, validated_to

class DateValidator:
    @staticmethod
    def validate_date_string(date_str: str) -> str:
        """
        Validate date string format (YYYY-MM-DD)
        """
        if not date_str:
            raise ValidationError("Date cannot be empty")
        
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, date_str):
            raise ValidationError(f"Date must be in YYYY-MM-DD format: {date_str}")
        
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if date is not in the future
            if parsed_date.date() > date.today():
                raise ValidationError(f"Date cannot be in the future: {date_str}")
            
            # Check if date is not too old (Frankfurter data starts from 1999-01-04)
            min_date = date(1999, 1, 4)
            if parsed_date.date() < min_date:
                raise ValidationError(f"Date cannot be earlier than 1999-01-04: {date_str}")
            
        except ValueError as e:
            if "time data" in str(e):
                raise ValidationError(f"Invalid date: {date_str}")
            raise ValidationError(f"Date validation error: {str(e)}")
        
        return date_str

class QueryValidator:
    @staticmethod
    def validate_session_id(session_id: str) -> str:
        """
        Validate session ID format
        """
        if not session_id:
            raise ValidationError("Session ID cannot be empty")
        
        session_id = session_id.strip()
        
        if len(session_id) < 10 or len(session_id) > 100:
            raise ValidationError(f"Session ID length must be between 10 and 100 characters: {len(session_id)}")
        
        # Allow alphanumeric and hyphens for UUID format
        if not re.match(r'^[a-zA-Z0-9\-_]+$', session_id):
            raise ValidationError(f"Session ID contains invalid characters: {session_id}")
        
        return session_id
    
    @staticmethod
    def validate_user_message(message: str) -> str:
        """
        Validate user input message
        """
        if not message:
            raise ValidationError("Message cannot be empty")
        
        message = message.strip()
        
        if len(message) == 0:
            raise ValidationError("Message cannot be only whitespace")
        
        if len(message) > 1000:
            raise ValidationError(f"Message is too long (max 1000 characters): {len(message)}")
        
        # Check for potentially malicious content
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
        ]
        
        message_lower = message.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, message_lower):
                raise ValidationError("Message contains potentially malicious content")
        
        return message

class ConversionExtractor:
    """
    Utility class for extracting currency conversion requests from text
    """
    
    # Enhanced regex patterns for different conversion formats
    CONVERSION_PATTERNS = [
        # "100 USD to EUR", "50.5 GBP in JPY"
        r'(\d+(?:\.\d+)?)\s*([a-zA-Z]{3})\s+(?:to|in|into)\s+([a-zA-Z]{3})',
        # "convert 100 USD to EUR", "change 50 GBP to JPY"
        r'(?:convert|change)\s+(\d+(?:\.\d+)?)\s*([a-zA-Z]{3})\s+(?:to|in|into)\s+([a-zA-Z]{3})',
        # "100 dollars to euros" (common currency names)
        r'(\d+(?:\.\d+)?)\s*(dollars?|euros?|pounds?|yen)\s+(?:to|in|into)\s+(dollars?|euros?|pounds?|yen)',
    ]
    
    CURRENCY_NAME_MAP = {
        'dollar': 'USD', 'dollars': 'USD',
        'euro': 'EUR', 'euros': 'EUR',
        'pound': 'GBP', 'pounds': 'GBP',
        'yen': 'JPY'
    }
    
    @classmethod
    def extract_conversions(cls, text: str) -> List[Tuple[float, str, str]]:
        """
        Extract all currency conversions from text
        Returns list of (amount, from_currency, to_currency) tuples
        """
        conversions = []
        text_lower = text.lower()
        
        for pattern in cls.CONVERSION_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                try:
                    amount_str, from_curr, to_curr = match
                    amount = float(amount_str)
                    
                    # Convert currency names to codes if needed
                    from_currency = cls.CURRENCY_NAME_MAP.get(from_curr.lower(), from_curr.upper())
                    to_currency = cls.CURRENCY_NAME_MAP.get(to_curr.lower(), to_curr.upper())
                    
                    # Validate the extracted conversion
                    validated = CurrencyValidator.validate_conversion_request(
                        amount, from_currency, to_currency
                    )
                    conversions.append(validated)
                    
                except (ValueError, ValidationError) as e:
                    logger.warning(f"Skipping invalid conversion in text: {match} - {e}")
                    continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_conversions = []
        for conv in conversions:
            if conv not in seen:
                seen.add(conv)
                unique_conversions.append(conv)
        
        return unique_conversions
    
    @classmethod
    def has_currency_context(cls, text: str) -> bool:
        """
        Check if text contains currency-related context
        """
        currency_keywords = [
            'convert', 'conversion', 'exchange', 'rate', 'currency', 'money',
            'dollar', 'euro', 'pound', 'yen', 'usd', 'eur', 'gbp', 'jpy'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in currency_keywords)