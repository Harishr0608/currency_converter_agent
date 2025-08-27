import time
from typing import Dict, List, Optional
from datetime import datetime
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.conversations = {}

    def get_conversation(self, session_id: str) -> list:
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        return self.conversations[session_id]

    def add_message(self, session_id: str, message: dict):
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        self.conversations[session_id].append(message)

    def clear_conversation(self, session_id: str):
        self.conversations[session_id] = []