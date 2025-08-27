import httpx
import re
from typing import Dict, List, Tuple
import logging
from datetime import datetime

from app.config.settings import settings

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self, base_url: str = settings.FRANKFURTER_BASE_URL):
        self.base_url = base_url
        self.timeout = 30.0
        self.supported_currencies = set([
            "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR",
            "NZD", "SGD", "HKD", "SEK", "KRW", "NOK", "MXN", "BRL", "PLN"
        ])

    async def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict:
        """Convert currency using Frankfurter API"""
        try:
            if from_currency not in self.supported_currencies:
                raise ValueError(f"Unsupported source currency: {from_currency}")
            if to_currency not in self.supported_currencies:
                raise ValueError(f"Unsupported target currency: {to_currency}")

            logger.info(f"Converting {amount} {from_currency} to {to_currency}")
            url = f"{self.base_url}/latest"
            params = {
                "amount": amount,
                "from": from_currency,
                "to": to_currency
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "amount": amount,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "converted_amount": round(data["rates"][to_currency], 2),
                    "exchange_rate": round(data["rates"][to_currency] / amount, 6),
                    "date": data.get("date", datetime.now().strftime("%Y-%m-%d"))
                }
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Currency conversion error: {str(e)}")
            raise ValueError(f"Error converting {from_currency} to {to_currency}")

    async def get_supported_currencies(self) -> Dict[str, str]:
        """
        Get list of all supported currencies
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/currencies"
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching supported currencies: {e}")
            raise Exception(f"Failed to fetch supported currencies: {str(e)}")
    
    async def get_historical_rate(self, date_str: str, from_currency: str, to_currency: str) -> Dict:
        """
        Get historical exchange rate for a specific date
        """
        try:
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            # Validate date format
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                if parsed_date > datetime.now():
                    raise ValueError("Cannot get exchange rates for future dates")
            except ValueError as ve:
                if "time data" in str(ve):
                    raise ValueError("Invalid date format. Use YYYY-MM-DD")
                raise
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/{date_str}"
                params = {
                    "from": from_currency,
                    "to": to_currency
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if to_currency not in data["rates"]:
                    raise ValueError(f"Exchange rate not available for {from_currency} to {to_currency} on {date_str}")
                
                exchange_rate = data["rates"][to_currency]
                
                return {
                    "date": data["date"],
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "exchange_rate": exchange_rate
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid request: {e.response.text}")
            else:
                logger.error(f"HTTP error during historical rate fetch: {e}")
                raise Exception(f"Historical rate service error: {e}")
                
        except Exception as e:
            logger.error(f"Error fetching historical rate: {e}")
            raise Exception(f"Failed to fetch historical rate: {str(e)}")
    
    async def get_latest_rates(self, base_currency: str = "EUR") -> Dict:
        """
        Get latest exchange rates for a base currency
        """
        try:
            base_currency = base_currency.upper()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}/latest"
                params = {"from": base_currency}
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching latest rates: {e}")
            raise Exception(f"Failed to fetch latest rates: {str(e)}")
    
    async def convert_multiple_currencies(self, conversions: List[Dict]) -> List[Dict]:
        """
        Convert multiple currencies concurrently
        """
        try:
            tasks = []
            for conversion in conversions:
                task = self.convert_currency(
                    amount=conversion["amount"],
                    from_currency=conversion["from_currency"],
                    to_currency=conversion["to_currency"]
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in conversion {i}: {result}")
                    final_results.append({
                        "error": str(result),
                        "conversion": conversions[i]
                    })
                else:
                    final_results.append(result)
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error in multiple currency conversion: {e}")
            raise Exception(f"Multiple currency conversion failed: {str(e)}")
    
    def parse_conversion_query(self, query: str) -> List[Tuple[float, str, str]]:
        """Parse currency conversion query with support for multiple conversions"""
        conversions = []
        
        # Split query into separate conversion requests
        conversion_requests = [req.strip() for req in query.split(" and ")]
        
        for request in conversion_requests:
            # Pattern for single conversion: "100 USD to EUR" or "convert 100 USD to EUR"
            pattern = r"(?:convert\s+)?(\d+(?:\.\d+)?)\s+(\w{3})\s+to\s+(\w{3})"
            match = re.match(pattern, request.strip(), re.IGNORECASE)
            
            if match:
                amount = float(match.group(1))
                from_curr = match.group(2).upper()
                to_curr = match.group(3).upper()
                conversions.append((amount, from_curr, to_curr))
            else:
                raise ValueError(
                    f"Invalid conversion format: '{request}'. "
                    "Use format: '100 USD to EUR' or '100 USD to EUR and 50 GBP to JPY'"
                )
        
        if not conversions:
            raise ValueError("No valid currency conversions found in query")
            
        return conversions
    
    async def batch_convert_currencies(self, conversions: List[Tuple[float, str, str]]) -> List[Dict]:
        """Convert multiple currencies in batch"""
        results = []
        for amount, from_curr, to_curr in conversions:
            try:
                result = await self.convert_currency(amount, from_curr, to_curr)
                results.append(result)
            except Exception as e:
                logger.error(f"Error converting {amount} {from_curr} to {to_curr}: {str(e)}")
                results.append({
                    "error": str(e),
                    "amount": amount,
                    "from_currency": from_curr,
                    "to_currency": to_curr
                })
        return results