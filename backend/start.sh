#!/bin/bash

echo "Environment variables:"
echo "NEBIUS_API_KEY is set: ${NEBIUS_API_KEY:0:10}..."
echo "DB_CONNECTION is set: ${DB_CONNECTION:0:20}..."
echo "PORT: $PORT"

# Start the application
exec python server/app.py --port "${PORT:-4000}" 