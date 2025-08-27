# 🤖 AI Currency Converter Agent

A sophisticated currency conversion application powered by FastAPI, Streamlit, OpenRouter LLM with function calling, and Frankfurter API.

## ✨ Features

- 🔄 **Real-time Currency Conversion**: Get up-to-date exchange rates
- 🚀 **Multi-Conversion Support**: Handle multiple currency conversions in a single query
- 💬 **Conversational Interface**: Natural language processing with AI
- 📊 **Historical Rates**: Access historical exchange rate data
- 🌍 **30+ Currencies**: Support for major global currencies
- 💾 **Session Memory**: Maintains conversation context
- 🎨 **Modern UI**: Beautiful Streamlit interface
- ⚡ **Async Processing**: Fast, non-blocking operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │◄──►│    FastAPI       │◄──►│   OpenRouter    │
│   Frontend      │    │    Backend       │    │   LLM API       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Frankfurter    │
                       │   Currency API   │
                       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenRouter API key (provided in the code)

### Option 1: One-Command Start (Recommended)

```bash
# Clone the project (or create the structure)
# Make the start script executable
chmod +x start.sh

# Start both backend and frontend
./start.sh
```

This will:
- Create virtual environments for both backend and frontend
- Install all dependencies
- Start FastAPI backend on port 8003
- Start Streamlit frontend on port 8501
- Display access URLs and usage examples

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

#### Frontend Setup

```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 🔧 Configuration

Copy `.env.example` to `.env` and customize:

```env
# Your OpenRouter API key is already provided
OPENROUTER_API_KEY=your-openai-key
OPENROUTER_MODEL=openai/gpt-5-chat
TEMPERATURE=0.1
MAX_TOKENS=500
```

## 💡 Usage Examples

### Single Conversion
```
Convert 100 USD to EUR
```

### Multiple Conversions (Key Feature!)
```
Convert 100 USD to EUR and 200 GBP to JPY
1000 INR to USD, EUR, and GBP
```

## 🎯 Key Features Deep Dive

### Multi-Conversion Intelligence

The system uses a sophisticated approach to handle multiple currency conversions:

1. **Regex Parsing**: Extracts all conversion patterns from user input
2. **Direct Processing**: Bypasses LLM for detected conversions for reliability
3. **Concurrent Execution**: Processes multiple conversions simultaneously
4. **Fallback Support**: Uses LLM function calling for complex queries

### Function Calling Architecture

- **Smart Detection**: Automatically determines when to use direct processing vs LLM
- **Tool Integration**: OpenRouter LLM with function calling capabilities
- **Error Handling**: Robust error handling with user-friendly messages
- **Context Awareness**: Maintains conversation context for follow-up questions

## 📚 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8003/docs
- **ReDoc Documentation**: http://localhost:8003/redoc

### Key Endpoints

- `POST /api/v1/chat/completions` - Main chat endpoint
- `GET /api/v1/conversations/{session_id}` - Get conversation history
- `POST /api/v1/conversations/{session_id}/clear` - Clear conversation
- `GET /api/v1/health` - Health check

## 🔍 Project Structure

```
currency_converter_agent/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── models/                 # Pydantic models
│   │   ├── services/               # Business logic
│   │   │   ├── llm_service.py      # Multi-conversion logic
│   │   │   ├── currency_service.py # Frankfurter integration
│   │   │   └── conversation_service.py
│   │   ├── utils/                  # Utilities
│   │   └── config/                 # Configuration
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py           # Main Streamlit app
│   ├── components/                # UI components
│   ├── utils/                     # Frontend utilities
│   └── requirements.txt
├── start.sh                       # One-command startup
├── .env.example                   # Environment template
└── README.md
```

## 🧪 Testing

Test the multi-conversion feature with:

```bash
# Example that should return TWO conversions
curl -X POST "http://localhost:8003/api/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Convert 100 USD to EUR and 200 GBP to JPY",
       "session_id": "test-session"
     }'
```

## 🌟 Advanced Features

### Session Management
- Automatic session creation and cleanup
- Conversation history persistence
- Context-aware follow-up questions

### Error Handling
- Graceful API failure handling
- User-friendly error messages
- Automatic retry mechanisms

### Performance Optimization
- Async processing throughout
- Concurrent currency conversions
- Efficient session management

## 🚀 Deployment

### Docker (Optional)

```dockerfile
# Example Dockerfile for backend
FROM python:3.9-slim

WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt

EXPOSE 8003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Production Considerations

- Set `DEBUG=False` in production
- Use proper secrets management
- Implement rate limiting
- Add monitoring and logging
- Use reverse proxy (nginx)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 APIs Used

- **OpenRouter**: LLM with function calling
- **Frankfurter**: Free currency conversion API
- **FastAPI**: Modern Python web framework
- **Streamlit**: Interactive web applications

## ⚡ Performance Notes

- Backend typically responds in <500ms
- Multiple conversions processed concurrently
- Session data stored in memory (Redis recommended for production)
- Automatic cleanup of expired sessions

## 🐛 Screenshot

<img width="1920" height="1131" alt="Screenshot 2025-08-27 at 12 16 17" src="https://github.com/user-attachments/assets/bcb2aff9-33b6-4da3-932e-8f697d5d3725" />
