#!/bin/bash
# Simple HTTP server script for the test UI

echo "Starting HTTP server for Test UI..."
echo ""
echo "Open your browser and go to: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 -m http.server 8080

