#!/bin/bash

echo "🚀 Starting Attendeely Backend Development Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Check if database is accessible
echo "🔍 Checking database connection..."
python3 -c "
from app.core.config import settings
from sqlalchemy import create_engine
try:
    engine = create_engine(settings.DATABASE_URL)
    conn = engine.connect()
    conn.close()
    print('✅ Database connection successful!')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please check your DATABASE_URL in .env')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "🌟 Starting server at http://localhost:8000"
echo "📚 API Docs available at http://localhost:8000/docs"
echo "📖 ReDoc available at http://localhost:8000/redoc"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
