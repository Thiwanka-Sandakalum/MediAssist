#!/usr/bin/env bash
# MediAssist Dashboard - Quick Start Script
# Usage: bash dashboard_start.sh

set -e

cd "$(dirname "$0")"

echo "🏥 MediAssist Dashboard - Starting..."
echo ""

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate venv
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "✅ Installing dependencies..."
pip install -e . -q

# Set environment variables for development
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-test-key-for-demo}"
export LOG_LEVEL="INFO"
export DATABASE_URL="postgresql://localhost/mediassist_dev"
export API_HOST="127.0.0.1"
export API_PORT="8000"

echo ""
echo "============================================================"
echo "🚀 MediAssist Pharmacy Dashboard"
echo "============================================================"
echo ""
echo "IMPORTANT: Database not required for MVP testing"
echo "The dashboard will use in-memory workflow storage"
echo ""
echo "Starting FastAPI server..."
echo "Open your browser to: http://localhost:8000"
echo ""
echo "Features available:"
echo "  📋 Prescription Queue - Submit and track prescriptions"
echo "  ✅ HITL Approval - Review and approve high-risk prescriptions"
echo "  📊 Dashboard - View metrics and statistics"
echo ""
echo "API Docs (Swagger): http://localhost:8000/docs"
echo "ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Start the API server
python run_api.py --reload --host 127.0.0.1 --port 8000
