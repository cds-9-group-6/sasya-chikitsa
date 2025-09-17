#!/bin/bash

# Start the Ollama server in the background
ollama serve &

# Wait a few seconds for the server to start
sleep 5  # you might need 10 seconds on slower machines

# Pull the model
ollama pull llama3.1:8b

echo "Ollama model is ready!"

# Keep the container running to serve requests
wait $!

