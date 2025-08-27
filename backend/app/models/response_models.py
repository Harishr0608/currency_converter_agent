from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.request_models import Message

class ChatResponse(BaseModel):
    response: str
    session_id: str

class ConversationResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    messages: List[Message] = Field(default=[], description="Conversation history")
    total_messages: int = Field(default=0, description="Total number of messages")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_messages = len(self.messages)

class CurrencyConversionResponse(BaseModel):
    amount: float = Field(..., description="Original amount")
    from_currency: str = Field(..., description="Source currency")
    to_currency: str = Field(..., description="Target currency")
    converted_amount: float = Field(..., description="Converted amount")
    exchange_rate: float = Field(..., description="Exchange rate used")
    date: str = Field(..., description="Date of exchange rate")
    
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())