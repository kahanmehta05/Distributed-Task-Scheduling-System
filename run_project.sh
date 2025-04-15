#!/bin/bash

# Set base directory
BASE_DIR=~/Downloads/distributed-task-scheduling-system

# Start Redis if not running
if ! redis-cli ping | grep -q PONG; then
  echo "🔄 Starting Redis..."
  brew services start redis
  sleep 2
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source $BASE_DIR/.venv/bin/activate

# Start API server
echo "🚀 Launching API server..."
osascript -e "tell app \"Terminal\" to do script \"cd $BASE_DIR/backend && source ../.venv/bin/activate && python -m client_interface.api\""

# Start 3 worker nodes
for i in 1 2 3
do
  echo "🔧 Starting Worker $i..."
  osascript -e "tell app \"Terminal\" to do script \"cd $BASE_DIR/backend && source ../.venv/bin/activate && python -m worker_node.worker\""
done

# Start frontend server
echo "🌐 Starting frontend server..."
osascript -e "tell app \"Terminal\" to do script \"cd $BASE_DIR/frontend && python3 -m http.server 8000\""

echo "✅ All services started! Open http://localhost:8000/dashboard.html in your browser."
