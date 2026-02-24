#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")"

# Check if .venv exists
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Error: .venv directory not found."
    echo "Please create it using: python3 -m venv .venv"
    exit 1
fi

# Run the streamlit app
echo "🚀 Starting Streamlit app..."
streamlit run main.py
