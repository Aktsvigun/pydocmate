# Docker Setup for PyDocAss

This directory contains Docker configuration files to run both the frontend and backend of the PyDocAss application.

## Prerequisites

- Docker
- Docker Compose

## Configuration

The setup consists of:

- Frontend service running on port 3000
- Backend service running on port 4000

## Running the Application

From the root directory of the project, run:

```bash
docker-compose -f docker/docker-compose.yml up
```

This will:
1. Build the Docker images if they don't exist
2. Start the backend service on port 4000
3. Start the frontend service on port 3000

## Development Mode

The configuration is set up for development, with volume mounts that allow you to make changes to the code and see them reflected immediately:

- Frontend changes will trigger Next.js hot reload
- Backend changes will require restarting the container (you can use `docker-compose restart backend`)

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:4000

## Stopping the Application

```bash
docker-compose -f docker/docker-compose.yml down
```

## Building for Production

For production deployment, you should modify the Dockerfiles to build optimized versions:

- For the frontend, use `npm run build` followed by `npm run start` 
- For the backend, consider using a WSGI server like Gunicorn 