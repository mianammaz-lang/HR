#!/bin/bash
set -e

echo "🧠 Starting Talent Pool Management System..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required. Please install Python 3.11+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required. Please install Node 18+"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying .env.example — edit it and set"
    echo "   DATABASE_URL / JWT_SECRET before continuing."
    cp .env.example .env
    exit 1
fi

# Backend setup
echo "📦 Setting up backend..."
cd api
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null
pip install -q -r requirements.txt

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start backend in background
echo "🚀 Starting backend on port 8000..."
cd ../api
set -a; source ../.env; set +a
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
echo "🚀 Starting frontend on port 3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Application started!"
echo ""
echo "   🌐 Frontend:  http://localhost:3000"
echo "   📡 Backend:   http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/api/docs"
echo ""
echo "   No admin user exists yet — see README.md 'First-time setup' to"
echo "   create one via the protected /api/admin/seed endpoint."
echo ""
echo "   Press Ctrl+C to stop all services"

# Wait for signals
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
