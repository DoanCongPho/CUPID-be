#!/bin/bash
# Start Django with Daphne ASGI server for WebSocket support

echo "🚀 Starting CUPID Backend with WebSocket Support..."
echo "📡 Server will run on http://127.0.0.1:8000"
echo "🔌 WebSocket endpoint: ws://127.0.0.1:8000/ws/chats/<chat_id>/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
poetry run daphne -b 127.0.0.1 -p 8000 config.asgi:application
