import httpx
import asyncio
from typing import Dict, Optional, List
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30.0
        self._connection_status = False
        
    async def chat_completion(self, request_data: Dict) -> Optional[Dict]:
        """
        Send chat completion request to FastAPI backend
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/chat/completions",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                self._connection_status = True
                result = response.json()
                logger.info(f"Chat completion successful for session: {request_data.get('session_id')}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in chat completion: {e.response.status_code} - {e.response.text}")
            self._connection_status = False
            
            # Parse error response if available
            try:
                error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            
            return {
                "response": f"I encountered an error processing your request: {error_detail}",
                "error": True
            }
            
        except httpx.TimeoutException:
            logger.error("Timeout in chat completion request")
            self._connection_status = False
            return {
                "response": "Request timed out. The server might be busy. Please try again.",
                "error": True
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in chat completion: {e}")
            self._connection_status = False
            return {
                "response": f"An unexpected error occurred: {str(e)}",
                "error": True
            }
    
    async def get_conversation(self, session_id: str) -> Optional[Dict]:
        """
        Get conversation history for a session
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/conversations/{session_id}"
                )
                response.raise_for_status()
                
                self._connection_status = True
                result = response.json()
                logger.info(f"Retrieved conversation for session: {session_id}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving conversation: {e}")
            self._connection_status = False
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            self._connection_status = False
            return None
    
    async def clear_conversation(self, session_id: str) -> bool:
        """
        Clear conversation history for a session
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/conversations/{session_id}/clear"
                )
                response.raise_for_status()
                
                self._connection_status = True
                logger.info(f"Cleared conversation for session: {session_id}")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error clearing conversation: {e}")
            self._connection_status = False
            return False
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            self._connection_status = False
            return False
    
    async def health_check(self) -> Optional[Dict]:
        """
        Check API health status
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/health")
                response.raise_for_status()
                
                self._connection_status = True
                result = response.json()
                logger.debug("Health check successful")
                return result
                
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self._connection_status = False
            return None
    
    def is_connected(self) -> bool:
        """
        Check if client is connected to API
        """
        return self._connection_status
    
    async def test_connection(self) -> Dict:
        """
        Test connection to API and return detailed status
        """
        try:
            start_time = datetime.now()
            health_result = await self.health_check()
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds() * 1000  # ms
            
            if health_result:
                return {
                    "connected": True,
                    "status": health_result.get("status", "unknown"),
                    "version": health_result.get("version", "unknown"),
                    "response_time_ms": round(response_time, 2),
                    "message": "Connection successful"
                }
            else:
                return {
                    "connected": False,
                    "status": "unhealthy",
                    "response_time_ms": round(response_time, 2),
                    "message": "Health check failed"
                }
                
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "message": str(e)
            }
    
    async def validate_session(self, session_id: str) -> bool:
        """
        Validate if session exists on server
        """
        try:
            result = await self.get_conversation(session_id)
            return result is not None
        except:
            return False
    
    async def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get session statistics (if endpoint exists)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/conversations/{session_id}/stats"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
                    
        except:
            # Stats endpoint might not exist, return None
            return None
    
    def set_base_url(self, base_url: str) -> None:
        """
        Update base URL for API calls
        """
        self.base_url = base_url.rstrip('/')
        self._connection_status = False  # Reset connection status
        logger.info(f"Updated API base URL to: {self.base_url}")
    
    def set_timeout(self, timeout: float) -> None:
        """
        Update request timeout
        """
        self.timeout = timeout
        logger.info(f"Updated API timeout to: {timeout}s")
    
    async def batch_requests(self, requests: List[Dict]) -> List[Dict]:
        """
        Send multiple requests concurrently (if needed)
        """
        try:
            tasks = []
            for request in requests:
                if request.get("type") == "chat":
                    task = self.chat_completion(request.get("data"))
                elif request.get("type") == "conversation":
                    task = self.get_conversation(request.get("session_id"))
                else:
                    continue
                tasks.append(task)
            
            if not tasks:
                return []
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "error": str(result),
                        "request_index": i
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in batch requests: {e}")
            return [{"error": str(e)} for _ in requests]