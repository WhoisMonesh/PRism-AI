#!/bin/bash

set -e

echo "🚀 PRism AI - Starting..."
echo ""

if [ ! -f .env ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your credentials:"
    echo "   - GITHUB_TOKEN"
    echo "   - GITHUB_WEBHOOK_SECRET"
    echo ""
    echo "Then run this script again."
    exit 0
fi

echo "📦 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "🤖 Checking if Ollama has models..."
if ! docker exec ollama ollama list | grep -q "llama3.1"; then
    echo "📥 Pulling llama3.1 model (this may take a few minutes)..."
    docker exec -it ollama ollama pull llama3.1
else
    echo "✅ llama3.1 already available"
fi

echo ""
echo "🎉 PRism AI is ready!"
echo ""
echo "📍 Access points:"
echo "   - Frontend UI:  http://localhost:5173"
echo "   - Backend API:  http://localhost:8000"
echo "   - API Docs:     http://localhost:8000/docs"
echo "   - Health Check: http://localhost:8000/api/v1/health"
echo ""
echo "📚 Next steps:"
echo "   1. Open http://localhost:5173"
echo "   2. Go to Settings and verify LLM connection"
echo "   3. Test a manual review in the Review tab"
echo "   4. Configure webhooks in your Git provider"
echo ""
echo "📖 Full documentation: README.md"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f prism-ai"
