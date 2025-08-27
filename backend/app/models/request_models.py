from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
import uuid

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="User message for currency conversion")
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Session ID for conversation continuity")
    
    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class ConversationRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to retrieve conversation")

class CurrencyConversionRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to convert")
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    
    @validator('from_currency', 'to_currency')
    def validate_currency_codes(cls, v):
        return v.upper().strip()

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)
    timestamp: Optional[str] = None