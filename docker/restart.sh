#!/bin/bash

cd "$(dirname "$0")"

echo "Stopping and removing any existing Docker containers..."
docker-compose down

echo "Checking if ports 3000 and 4000 are in use..."

# Check if port 3000 is in use
if lsof -i :3000 > /dev/null; then
  echo "Port 3000 is in use. Attempting to free it..."
  lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs -r kill -9
fi

# Check if port 4000 is in use
if lsof -i :4000 > /dev/null; then
  echo "Port 4000 is in use. Attempting to free it..."
  lsof -i :4000 | grep LISTEN | awk '{print $2}' | xargs -r kill -9
fi

echo "Ports checked. Starting docker containers..."
docker-compose up -d

echo "Docker containers started in background. To view logs, run:"
echo "docker-compose logs -f" 