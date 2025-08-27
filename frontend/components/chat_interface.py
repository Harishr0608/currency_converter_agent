import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)

class ChatInterface:
    def __init__(self):
        self.message_limit = 50  # Limit displayed messages for performance
        
    def display_messages(self, messages: List[Dict]) -> None:
        """
        Display chat messages in the Streamlit interface
        """
        try:
            # Limit messages for performance
            display_messages = messages[-self.message_limit:] if len(messages) > self.message_limit else messages
            
            for message in display_messages:
                self._render_message(message)
                
        except Exception as e:
            logger.error(f"Error displaying messages: {e}")
            st.error("Error displaying conversation history")
    
    def _render_message(self, message: Dict) -> None:
        """
        Render individual message with appropriate styling
        """
        try:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp")
            
            with st.chat_message(role):
                if role == "assistant":
                    self._render_assistant_message(content)
                else:
                    self._render_user_message(content)
                
                # Show timestamp if available
                if timestamp:
                    self._render_timestamp(timestamp)
                    
        except Exception as e:
            logger.error(f"Error rendering message: {e}")
            st.error("Error rendering message")
    
    def _render_assistant_message(self, content: str) -> None:
        """
        Render assistant message with special formatting for currency conversions
        """
        try:
            # Check if content contains currency conversion results
            if self._is_conversion_response(content):
                self._render_conversion_response(content)
            else:
                st.markdown(content)
                
        except Exception as e:
            logger.error(f"Error rendering assistant message: {e}")
            st.write(content)  # Fallback to simple write
    
    def _render_user_message(self, content: str) -> None:
        """
        Render user message with simple formatting
        """
        st.write(content)
    
    def _render_conversion_response(self, content: str) -> None:
        """
        Render currency conversion response with enhanced formatting
        """
        try:
            # Split content by conversion sections
            sections = content.split("**Conversion")
            
            if len(sections) > 1:
                # Multiple conversions
                for i, section in enumerate(sections[1:], 1):
                    self._render_single_conversion(f"Conversion {section}", i)
            else:
                # Single conversion or other response
                st.markdown(content)
                
        except Exception as e:
            logger.error(f"Error rendering conversion response: {e}")
            st.markdown(content)  # Fallback
    
    def _render_single_conversion(self, section: str, index: int) -> None:
        """
        Render a single currency conversion with styled container
        """
        try:
            # Parse conversion details
            conversion_data = self._parse_conversion_section(section)
            
            if conversion_data:
                with st.container():
                    st.markdown(f"""
                    <div class="conversion-result">
                        <h4>💱 Conversion {index}</h4>
                        <p><strong>{conversion_data['amount']} {conversion_data['from_currency']}</strong> = 
                        <strong style="color: #2e7d32; font-size: 1.2em;">{conversion_data['converted_amount']} {conversion_data['to_currency']}</strong></p>
                        <p>📊 Rate: 1 {conversion_data['from_currency']} = {conversion_data['exchange_rate']} {conversion_data['to_currency']}</p>
                        <p>📅 Date: {conversion_data.get('date', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Fallback rendering
                st.markdown(f"**Conversion {index}:**")
                st.markdown(section)
                
        except Exception as e:
            logger.error(f"Error rendering single conversion: {e}")
            st.markdown(f"**Conversion {index}:**")
            st.markdown(section)
    
    def _parse_conversion_section(self, section: str) -> Optional[Dict]:
        """
        Parse conversion section to extract structured data
        """
        try:
            # Regex patterns to extract conversion data
            amount_pattern = r'(\d+(?:\.\d+)?)\s+([A-Z]{3})\s+=\s+\*\*(\d+(?:\.\d+)?)\s+([A-Z]{3})\*\*'
            rate_pattern = r'1\s+([A-Z]{3})\s+=\s+(\d+(?:\.\d+)?)\s+([A-Z]{3})'
            date_pattern = r'Rate Date:\s*(\d{4}-\d{2}-\d{2})'
            
            amount_match = re.search(amount_pattern, section)
            rate_match = re.search(rate_pattern, section)
            date_match = re.search(date_pattern, section)
            
            if amount_match:
                return {
                    'amount': amount_match.group(1),
                    'from_currency': amount_match.group(2),
                    'converted_amount': amount_match.group(3),
                    'to_currency': amount_match.group(4),
                    'exchange_rate': rate_match.group(2) if rate_match else 'N/A',
                    'date': date_match.group(1) if date_match else 'N/A'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing conversion section: {e}")
            return None
    
    def _is_conversion_response(self, content: str) -> bool:
        """
        Check if content is a currency conversion response
        """
        conversion_indicators = [
            "💰", "💱", "📊", "Exchange Rate", "Conversion",
            "=", "Rate Date", "[A-Z]{3}"
        ]
        
        return any(indicator in content for indicator in conversion_indicators)
    
    def _render_timestamp(self, timestamp: str) -> None:
        """
        Render message timestamp
        """
        try:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%H:%M:%S")
            
            st.caption(f"🕒 {formatted_time}")
            
        except Exception as e:
            logger.warning(f"Error formatting timestamp: {e}")
            # Don't show timestamp if parsing fails
            pass
    
    def render_typing_indicator(self) -> None:
        """
        Show typing indicator for AI response
        """
        with st.chat_message("assistant"):
            st.write("🤔 Thinking...")
    
    def render_error_message(self, error_message: str) -> None:
        """
        Render error message with appropriate styling
        """
        st.markdown(f"""
        <div class="error-message">
            <h4>❌ Error</h4>
            <p>{error_message}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_success_message(self, success_message: str) -> None:
        """
        Render success message with appropriate styling
        """
        st.success(f"✅ {success_message}")
    
    def render_info_message(self, info_message: str) -> None:
        """
        Render informational message
        """
        st.info(f"ℹ️ {info_message}")
    
    def render_currency_list(self, currencies: Dict[str, str]) -> None:
        """
        Render supported currencies in a nice format
        """
        try:
            st.subheader("💰 Supported Currencies")
            
            # Create columns for better layout
            cols = st.columns(3)
            
            currency_items = list(currencies.items())
            items_per_col = len(currency_items) // 3 + 1
            
            for i, (code, name) in enumerate(currency_items):
                col_index = i // items_per_col
                if col_index < 3:  # Safety check
                    with cols[col_index]:
                        st.write(f"**{code}** - {name}")
                        
        except Exception as e:
            logger.error(f"Error rendering currency list: {e}")
            st.write("Error displaying currency list")
    
    def render_historical_rate(self, rate_data: Dict) -> None:
        """
        Render historical rate information
        """
        try:
            st.markdown(f"""
            <div class="conversion-result">
                <h4>📊 Historical Exchange Rate</h4>
                <p><strong>Date:</strong> {rate_data.get('date', 'N/A')}</p>
                <p><strong>Rate:</strong> 1 {rate_data.get('from_currency', 'N/A')} = 
                {rate_data.get('exchange_rate', 'N/A')} {rate_data.get('to_currency', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Error rendering historical rate: {e}")
            st.write(f"Historical rate: {rate_data}")
    
    def get_user_feedback(self) -> Optional[Dict]:
        """
        Get user feedback on the conversation
        """
        try:
            with st.expander("💬 Feedback"):
                col1, col2 = st.columns(2)
                
                with col1:
                    rating = st.selectbox(
                        "Rate this conversation:",
                        options=[None, 1, 2, 3, 4, 5],
                        format_func=lambda x: "Select rating..." if x is None else f"{'⭐' * x}"
                    )
                
                with col2:
                    helpful = st.radio(
                        "Was this helpful?",
                        options=[None, True, False],
                        format_func=lambda x: "Select..." if x is None else ("Yes" if x else "No")
                    )
                
                feedback_text = st.text_area("Additional comments (optional):")
                
                if st.button("Submit Feedback"):
                    if rating is not None or helpful is not None:
                        return {
                            "rating": rating,
                            "helpful": helpful,
                            "comments": feedback_text,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        st.warning("Please provide at least a rating or helpful indicator.")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user feedback: {e}")
            return None