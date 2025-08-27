import streamlit as st
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.session_key = "currency_converter_sessions"
        self.max_sessions = 10
        self.session_timeout_hours = 24
        
    def initialize_session_data(self) -> None:
        """
        Initialize session data in Streamlit session state
        """
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {}
    
    def create_session(self, session_id: str) -> Dict:
        """
        Create a new session with metadata
        """
        self.initialize_session_data()
        
        session_data = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
            "conversion_count": 0,
            "interactions": [],
            "metadata": {
                "user_agent": self._get_user_agent(),
                "timezone": self._get_timezone()
            }
        }
        
        st.session_state[self.session_key][session_id] = session_data
        
        # Cleanup old sessions
        self._cleanup_old_sessions()
        
        logger.info(f"Created new session: {session_id}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data by ID
        """
        self.initialize_session_data()
        
        sessions = st.session_state[self.session_key]
        if session_id in sessions:
            session_data = sessions[session_id]
            
            # Update last activity
            session_data["last_activity"] = datetime.now().isoformat()
            sessions[session_id] = session_data
            
            return session_data
        
        return None
    
    def add_interaction(self, session_id: str, user_input: str, ai_response: str) -> None:
        """
        Add interaction to session history
        """
        self.initialize_session_data()
        
        session_data = self.get_session(session_id)
        if not session_data:
            session_data = self.create_session(session_id)
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
            "input_length": len(user_input),
            "response_length": len(ai_response),
            "contains_conversion": self._contains_conversion(ai_response)
        }
        
        session_data["interactions"].append(interaction)
        session_data["message_count"] += 1
        session_data["last_activity"] = datetime.now().isoformat()
        
        if interaction["contains_conversion"]:
            session_data["conversion_count"] += 1
        
        # Keep only last 50 interactions per session
        if len(session_data["interactions"]) > 50:
            session_data["interactions"] = session_data["interactions"][-50:]
        
        st.session_state[self.session_key][session_id] = session_data
        
        logger.debug(f"Added interaction to session {session_id}")
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear session data
        """
        self.initialize_session_data()
        
        sessions = st.session_state[self.session_key]
        if session_id in sessions:
            del sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        
        return False
    
    def get_session_stats(self, session_id: str) -> Dict:
        """
        Get session statistics
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return {"exists": False}
        
        interactions = session_data.get("interactions", [])
        
        stats = {
            "exists": True,
            "session_id": session_id,
            "created_at": session_data.get("created_at"),
            "last_activity": session_data.get("last_activity"),
            "total_messages": session_data.get("message_count", 0),
            "conversion_count": session_data.get("conversion_count", 0),
            "total_interactions": len(interactions),
            "average_input_length": 0,
            "average_response_length": 0,
            "session_duration": self._calculate_session_duration(session_data)
        }
        
        if interactions:
            stats["average_input_length"] = sum(i.get("input_length", 0) for i in interactions) / len(interactions)
            stats["average_response_length"] = sum(i.get("response_length", 0) for i in interactions) / len(interactions)
        
        return stats
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get all session data (summary)
        """
        self.initialize_session_data()
        
        sessions = st.session_state[self.session_key]
        session_list = []
        
        for session_id, session_data in sessions.items():
            session_summary = {
                "id": session_id,
                "created_at": session_data.get("created_at"),
                "last_activity": session_data.get("last_activity"),
                "message_count": session_data.get("message_count", 0),
                "conversion_count": session_data.get("conversion_count", 0)
            }
            session_list.append(session_summary)
        
        # Sort by last activity
        session_list.sort(key=lambda x: x["last_activity"], reverse=True)
        
        return session_list
    
    def export_session_data(self, session_id: str) -> Optional[str]:
        """
        Export session data as JSON string
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        
        try:
            return json.dumps(session_data, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return None
    
    def import_session_data(self, session_data_json: str) -> Optional[str]:
        """
        Import session data from JSON string
        """
        try:
            session_data = json.loads(session_data_json)
            session_id = session_data.get("id")
            
            if not session_id:
                return None
            
            self.initialize_session_data()
            st.session_state[self.session_key][session_id] = session_data
            
            logger.info(f"Imported session data for: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error importing session data: {e}")
            return None
    
    def _cleanup_old_sessions(self) -> None:
        """
        Clean up old or excess sessions
        """
        try:
            sessions = st.session_state[self.session_key]
            
            # Remove sessions older than timeout
            cutoff_time = datetime.now() - timedelta(hours=self.session_timeout_hours)
            expired_sessions = []
            
            for session_id, session_data in sessions.items():
                last_activity = datetime.fromisoformat(session_data.get("last_activity", "1970-01-01"))
                if last_activity < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del sessions[session_id]
                logger.info(f"Removed expired session: {session_id}")
            
            # Remove excess sessions (keep most recent)
            if len(sessions) > self.max_sessions:
                session_items = list(sessions.items())
                session_items.sort(key=lambda x: x[1].get("last_activity", "1970-01-01"))
                
                excess_count = len(sessions) - self.max_sessions
                for i in range(excess_count):
                    session_id = session_items[i][0]
                    del sessions[session_id]
                    logger.info(f"Removed excess session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
    
    def _contains_conversion(self, text: str) -> bool:
        """
        Check if text contains currency conversion results
        """
        conversion_indicators = [
            "💰", "💱", "📊", "Exchange Rate", "Conversion",
            "=", "Rate Date"
        ]
        
        return any(indicator in text for indicator in conversion_indicators)
    
    def _calculate_session_duration(self, session_data: Dict) -> str:
        """
        Calculate session duration
        """
        try:
            created_at = datetime.fromisoformat(session_data.get("created_at", ""))
            last_activity = datetime.fromisoformat(session_data.get("last_activity", ""))
            
            duration = last_activity - created_at
            
            if duration.days > 0:
                return f"{duration.days} days, {duration.seconds // 3600} hours"
            elif duration.seconds >= 3600:
                return f"{duration.seconds // 3600} hours, {(duration.seconds % 3600) // 60} minutes"
            elif duration.seconds >= 60:
                return f"{duration.seconds // 60} minutes"
            else:
                return f"{duration.seconds} seconds"
                
        except Exception as e:
            logger.error(f"Error calculating session duration: {e}")
            return "Unknown"
    
    def _get_user_agent(self) -> str:
        """
        Get user agent (simplified for Streamlit)
        """
        try:
            # In Streamlit, we don't have direct access to request headers
            # Return a generic identifier
            return "Streamlit-App"
        except:
            return "Unknown"
    
    def _get_timezone(self) -> str:
        """
        Get user timezone (simplified)
        """
        try:
            # Return server timezone as we can't easily get client timezone in Streamlit
            return datetime.now().astimezone().tzinfo.tzname(None) or "UTC"
        except:
            return "UTC"