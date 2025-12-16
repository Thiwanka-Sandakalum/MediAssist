#!/bin/bash

# Quick Setup Script for MediAssist Backend
# This script helps you get started quickly

set -e  # Exit on error

echo "🏥 MediAssist Backend - Quick Setup"
echo "===================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed!"
    exit 1
fi

echo "✅ npm version: $(npm --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
npm install

echo ""
echo "✅ Dependencies installed!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created!"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo ""
    echo "To get a Gemini API key:"
    echo "1. Visit: https://aistudio.google.com/app/apikey"
    echo "2. Click 'Create API Key'"
    echo "3. Copy the key and paste it in .env"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Check if GEMINI_API_KEY is set
if grep -q "your_gemini_api_key_here" .env; then
    echo "⚠️  WARNING: GEMINI_API_KEY is not set in .env"
    echo "Please edit .env and add your API key before running the server."
    echo ""
else
    echo "✅ GEMINI_API_KEY appears to be set"
    echo ""
fi

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GEMINI_API_KEY (if not done)"
echo "2. Run 'npm run dev' to start the development server"
echo "3. Test with: curl -X POST http://localhost:3000/agent/chat \\"
echo "   -H 'Content-Type: application/json' \\"
echo "   -d '{\"message\": \"What are the side effects of ibuprofen?\"}'"
echo ""
echo "📚 Read USAGE.md for more information"
echo ""
