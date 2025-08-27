from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.request_models import ChatRequest, ConversationRequest
from app.models.response_models import ChatResponse, ConversationResponse, HealthResponse
from app.services.llm_service import LLMService
from app.services.conversation_service import ConversationService
from app.services.currency_service import CurrencyService
from app.config.settings import settings
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Currency Converter Agent",
    description="AI-powered currency converter with multi-conversion support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversation_service = ConversationService()
currency_service = CurrencyService()

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Currency Converter Agent API")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Currency Converter Agent API")

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Currency Converter Agent is running",
        version="1.0.0"
    )

@app.post("/api/v1/chat/completions", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Main endpoint for currency queries with multi-conversion support
    """
    try:
        logger.info(f"Received chat request for session: {request.session_id}")
        logger.info(f"User query: {request.message}")
        
        # Parse and process currency conversion
        try:
            conversions = currency_service.parse_conversion_query(request.message)
            results = await currency_service.batch_convert_currencies(conversions)
            
            # Format conversions
            conversion_lines = []
            rate_lines = []
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            for result in results:
                if "error" in result:
                    conversion_lines.append(f"❌ {result['error']}")
                else:
                    conversion_lines.append(
                        f"{result['amount']} {result['from_currency']} = "
                        f"{result['converted_amount']:.2f} {result['to_currency']}"
                    )
                    rate_lines.append(
                        f"1 {result['from_currency']} = "
                        f"{result['exchange_rate']:.4f} {result['to_currency']}"
                    )
            
            # Build response without using backslashes in f-strings
            response_parts = [
                f"🕒 {timestamp}",
                "",
                "\n".join(conversion_lines),
                "",
                "Exchange Rates:",
                "\n".join(rate_lines)
            ]
            response_text = "\n".join(response_parts)
            
        except ValueError as e:
            response_text = f"❌ {str(e)}"
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            response_text = "❌ Sorry, I encountered an error processing your request."
        
        response = ChatResponse(
            response=response_text,
            session_id=request.session_id
        )
        
        # Add messages to conversation
        conversation_service.add_message(request.session_id, {
            "role": "user",
            "content": request.message
        })
        conversation_service.add_message(request.session_id, {
            "role": "assistant",
            "content": response_text
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/v1/conversations/{session_id}", response_model=ConversationResponse)
async def get_conversation(session_id: str):
    """Retrieve chat history for a session"""
    try:
        conversation_history = ConversationService.get_conversation(session_id)
        return ConversationResponse(
            session_id=session_id,
            messages=conversation_history
        )
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/api/v1/conversations/{session_id}/clear")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    try:
        ConversationService.clear_conversation(session_id)
        return {"message": f"Conversation {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True
    )