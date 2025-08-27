import streamlit as st
import asyncio
import uuid
from datetime import datetime
from components.chat_interface import ChatInterface
from components.api_client import APIClient
from utils.session_manager import SessionManager
import logging
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Currency Converter",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .conversion-result {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    
    .error-message {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: #c62828;
    }
    
    .sidebar-info {
        background-color: #f1f8e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    
    if "chat_interface" not in st.session_state:
        st.session_state.chat_interface = ChatInterface()
    
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager()

def check_backend_health():
    """Check backend health status with retries"""
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get("http://localhost:8003/health", timeout=5)
            if response.status_code == 200:
                return True
            logger.warning(f"Backend health check failed (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError:
            logger.error(f"Backend connection failed (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.Timeout:
            logger.error(f"Backend request timed out (attempt {attempt + 1}/{MAX_RETRIES})")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    return False

def display_connection_status():
    """Display backend connection status with detailed information"""
    status_container = st.container()
    
    with status_container:
        if check_backend_health():
            st.success("✅ Connected to API")
        else:
            st.error("""
            ❌ Backend Connection Error
            
            Please check:
            1. Backend server is running (check terminal)
            2. Backend is accessible at http://localhost:8003
            3. No firewall blocking the connection
            
            Try running the backend with:
            ```
            cd backend
            uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
            ```
            """)
            st.stop()

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Check backend connection first
    display_connection_status()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Currency Converter</h1>
        <p>Powered by OpenRouter & Frankfurter API</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ Information")
        
        st.markdown("""
        <div class="sidebar-info">
            <h4>Features:</h4>
            <ul>
                <li>Real-time currency conversion</li>
                <li>Multiple conversions in one query</li>
                <li>Historical exchange rates</li>
                <li>Support for 30+ currencies</li>
                <li>Conversation memory</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Session info
        st.subheader("Session Information")
        st.info(f"Session ID: {st.session_state.session_id[:8]}...")
        st.info(f"Messages: {len(st.session_state.messages)}")
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "Convert 100 USD to EUR",
            "100 USD to EUR and 50 GBP to JPY",
            "Convert 100 USD to EUR and 200 GBP to JPY"
        ]
        
        for query in example_queries:
            if st.button(f"📝 {query}", key=f"example_{hash(query)}"):
                st.session_state.example_query = query
        
        # Clear conversation
        if st.button("🗑️ Clear Conversation", type="secondary"):
            if clear_conversation():
                st.rerun()
    
    # Main chat interface
    # Display conversation history
    st.session_state.chat_interface.display_messages(st.session_state.messages)
    
    # Handle example query
    user_input = ""
    if "example_query" in st.session_state:
        user_input = st.session_state.example_query
        del st.session_state.example_query
    
    # Chat input - moved outside of any container
    prompt = st.chat_input("Ask me about currency conversion...") or user_input
    
    if prompt:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Converting currencies..."):
                response = asyncio.run(get_ai_response(prompt))
                st.write(response)
        
        # Add assistant message to chat
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
    
    # Display connection status
    if st.session_state.api_client.is_connected():
        st.success("✅ Connected to API")
    else:
        st.error("❌ API Connection Error")

async def get_ai_response(user_input: str) -> str:
    """Get response from AI assistant"""
    try:
        api_client = st.session_state.api_client
        session_manager = st.session_state.session_manager
        
        # Prepare request data
        request_data = {
            "message": user_input,
            "session_id": st.session_state.session_id
        }
        
        # Make API call
        response = await api_client.chat_completion(request_data)
        
        if response and "response" in response:
            # Update session manager
            session_manager.add_interaction(
                st.session_state.session_id,
                user_input,
                response["response"]
            )
            return response["response"]
        else:
            return "I apologize, but I couldn't process your request. Please try again."
            
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        return f"I encountered an error: {str(e)}. Please try again."

def clear_conversation() -> bool:
    """Clear conversation history"""
    try:
        # Clear local session state
        st.session_state.messages = []
        
        # Clear server-side conversation
        api_client = st.session_state.api_client
        asyncio.run(api_client.clear_conversation(st.session_state.session_id))
        
        # Reset session manager
        st.session_state.session_manager.clear_session(st.session_state.session_id)
        
        st.success("Conversation cleared!")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        st.error(f"Error clearing conversation: {str(e)}")
        return False

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Built with ❤️ using FastAPI, Streamlit, OpenRouter, and Frankfurter API</p>
    <p>Real-time currency conversion with AI assistance</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()