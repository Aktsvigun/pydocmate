# Use the official Python image as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables for Python and default port
# (sensitive variables will come from .env via docker-compose)
ENV PYTHONUNBUFFERED=1
ENV PORT=4000

# Copy the entire application code
COPY . .

# Install the package in development mode (which also installs dependencies)
RUN pip install -e .

# Expose the port the app will run on
EXPOSE 4000

# Start the application
CMD ["python", "server/app.py", "--port", "$PORT"]
