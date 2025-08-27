#!/bin/bash

# Currency Converter Agent Startup Script

echo "🚀 Starting Currency Converter Agent..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update your OpenRouter API key in .env file"
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to install backend dependencies
install_backend_deps() {
    echo "📦 Installing backend dependencies..."
    cd backend
    
    echo "📥 Installing requirements..."
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "⚠️  Creating backend directory structure..."
        mkdir -p app
        touch app/__init__.py
        echo "fastapi
uvicorn[standard]
pydantic
httpx
python-dotenv" > requirements.txt
        pip install -r requirements.txt
    fi
    cd ..
}

# Function to install frontend dependencies
install_frontend_deps() {
    echo "📦 Installing frontend dependencies..."
    cd frontend
    
    echo "📥 Installing requirements..."
    pip install --upgrade pip
    
    
    cd ..
}

# Function to start backend
start_backend() {
    echo "🔧 Starting FastAPI backend..."
    cd backend
    
    # Start FastAPI with uvicorn
    uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload &
    BACKEND_PID=$!
    
    echo "⏳ Waiting for backend to start..."
    sleep 5
    
    # Check if backend started successfully
    if check_port 8003; then
        echo "✅ Backend started successfully on port 8003"
    else
        echo "❌ Backend failed to start"
        exit 1
    fi
    
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Streamlit frontend..."
    cd frontend
    
    # Start Streamlit
    streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
    FRONTEND_PID=$!
    
    echo "⏳ Waiting for frontend to start..."
    sleep 5
    
    # Check if frontend started successfully
    if check_port 8501; then
        echo "✅ Frontend started successfully on port 8501"
    else
        echo "❌ Frontend failed to start"
        exit 1
    fi
    
    cd ..
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔧 Stopping backend..."
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🎨 Stopping frontend..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill any remaining processes on our ports
    lsof -ti:8003 | xargs kill -9 2>/dev/null
    lsof -ti:8501 | xargs kill -9 2>/dev/null
    
    echo "👋 Goodbye!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo "🏗️  Setting up Currency Converter Agent..."
    
    # Check if Python3 is installed
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check if ports are available
    if check_port 8003; then
        echo "⚠️  Port 8003 is already in use. Please stop the service using this port."
        exit 1
    fi
    
    if check_port 8501; then
        echo "⚠️  Port 8501 is already in use. Please stop the service using this port."
        exit 1
    fi
    
    # Install dependencies
    echo "📚 Installing dependencies..."
    install_backend_deps
    install_frontend_deps
    
    # Start services
    echo "🚀 Starting services..."
    start_backend
    start_frontend
    
    # Display information
    echo ""
    echo "🎉 Currency Converter Agent is running!"
    echo ""
    echo "📍 Services:"
    echo "   🔧 Backend API:  http://localhost:8003"
    echo "   📚 API Docs:     http://localhost:8003/docs"
    echo "   🎨 Frontend UI:  http://localhost:8501"
    echo ""
    echo "🔍 Logs:"
    echo "   Backend PID: $BACKEND_PID"
    echo "   Frontend PID: $FRONTEND_PID"
    echo ""
    echo "💡 Usage Examples:"
    echo '   "Convert 100 USD to EUR"'
    echo '   "100 USD to EUR and 200 GBP to JPY"'
    echo '   "What currencies are supported?"'
    echo '   "Historical rate for USD to EUR on 2023-12-01"'
    echo ""
    echo "⏹️  Press Ctrl+C to stop all services"
    echo ""
    
    # Wait for processes
    wait
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi