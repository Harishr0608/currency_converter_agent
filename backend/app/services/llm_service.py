import httpx
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from app.config.settings import settings
from app.services.currency_service import CurrencyService
from app.utils.function_schemas import AVAILABLE_FUNCTIONS, SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.currency_service = CurrencyService()
        
        # Multi-conversion regex pattern (case-insensitive, global)
        self.conversion_pattern = r'(\d+(?:\.\d+)?)\s*([a-zA-Z]{3})\s*(?:to|in)\s*([a-zA-Z]{3})'
        
    async def process_query(self, query: str, conversation_history: List[Dict] = None) -> str:
        """
        Process user query with multi-conversion detection and handling
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Step 1: Parse query for currency conversions using regex
            conversions = self._extract_conversions(query)
            logger.info(f"Parsed conversions: {conversions}")
            
            if len(conversions) >= 1:
                # Direct conversion handling - skip LLM tool calling
                logger.info(f"Executing {len(conversions)} Frankfurter calls directly")
                results = await self.currency_service.convert_multiple_currencies(conversions)
                logger.info(f"Conversion results count: {len(results)}")
                
                response = self._format_multiple_conversions_response(results)
                logger.info(f"Final response preview: {response[:200]}...")
                return response
            
            # Step 2: No conversions detected - use LLM with tool calling
            logger.info("No direct conversions detected, using LLM with tool calling")
            return await self._process_with_llm(query, conversation_history)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}"
    
    def _extract_conversions(self, query: str) -> List[Dict]:
        """
        Extract all currency conversions from query using regex
        """
        conversions = []
        matches = re.findall(self.conversion_pattern, query, re.IGNORECASE)
        
        for match in matches:
            amount, from_currency, to_currency = match
            conversions.append({
                "amount": float(amount),
                "from_currency": from_currency.upper(),
                "to_currency": to_currency.upper()
            })
        
        return conversions
    
    def _format_multiple_conversions_response(self, results: List[Dict]) -> str:
        """
        Format multiple conversion results into a user-friendly response
        """
        if not results:
            return "I couldn't process any conversions from your request."
        
        response_parts = []
        
        for i, result in enumerate(results, 1):
            if "error" in result:
                response_parts.append(
                    f"**Conversion {i}:**\n"
                    f"❌ Error: {result['error']}\n"
                )
            else:
                response_parts.append(
                    f"**Conversion {i}:**\n"
                    f"💰 {result['amount']} {result['from_currency']} = "
                    f"**{result['converted_amount']} {result['to_currency']}**\n"
                    f"📊 Exchange Rate: 1 {result['from_currency']} = "
                    f"{result['exchange_rate']} {result['to_currency']}\n"
                    f"📅 Rate Date: {result['date']}\n"
                )
        
        return "\n".join(response_parts)
    
    async def _process_with_llm(self, query: str, conversation_history: List[Dict] = None) -> str:
        """
        Process query using LLM with tool/function calling
        """
        try:
            # Prepare messages
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages for context
            
            messages.append({"role": "user", "content": query})
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "tools": [{"type": "function", "function": func} for func in AVAILABLE_FUNCTIONS]
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                message = data["choices"][0]["message"]
                
                # Check if LLM wants to call functions
                if "tool_calls" in message and message["tool_calls"]:
                    logger.info(f"LLM returned {len(message['tool_calls'])} tool calls")
                    return await self._handle_tool_calls(message["tool_calls"])
                else:
                    return message.get("content", "I couldn't process your request.")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in LLM request: {e}")
            return "I'm having trouble connecting to the AI service. Please try again."
        except Exception as e:
            logger.error(f"Error in LLM processing: {e}")
            return "I encountered an error processing your request. Please try again."
    
    async def _handle_tool_calls(self, tool_calls: List[Dict]) -> str:
        """
        Handle multiple tool calls from LLM and aggregate results
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                
                if function_name == "convert_currency":
                    result = await self.currency_service.convert_currency(
                        amount=arguments["amount"],
                        from_currency=arguments["from_currency"],
                        to_currency=arguments["to_currency"]
                    )
                    results.append(result)
                    
                elif function_name == "get_supported_currencies":
                    currencies = await self.currency_service.get_supported_currencies()
                    return self._format_supported_currencies(currencies)
                    
                elif function_name == "get_historical_rate":
                    rate_data = await self.currency_service.get_historical_rate(
                        date_str=arguments["date"],
                        from_currency=arguments["from_currency"],
                        to_currency=arguments["to_currency"]
                    )
                    return self._format_historical_rate(rate_data)
                    
            except Exception as e:
                logger.error(f"Error executing tool call {function_name}: {e}")
                results.append({"error": str(e), "function": function_name})
        
        # Format all conversion results
        if results:
            return self._format_multiple_conversions_response(results)
        else:
            return "I couldn't execute the requested function calls."
    
    def _format_supported_currencies(self, currencies: Dict[str, str]) -> str:
        """
        Format supported currencies response
        """
        currency_list = []
        for code, name in sorted(currencies.items()):
            currency_list.append(f"• **{code}** - {name}")
        
        return f"Here are the supported currencies:\n\n" + "\n".join(currency_list)
    
    def _format_historical_rate(self, rate_data: Dict) -> str:
        """
        Format historical rate response
        """
        return (
            f"**Historical Exchange Rate**\n"
            f"📅 Date: {rate_data['date']}\n"
            f"💱 1 {rate_data['from_currency']} = {rate_data['exchange_rate']} {rate_data['to_currency']}\n"
        )