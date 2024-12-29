# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install pyOpenSSL

# Create necessary directories
RUN mkdir -p media static certificates

# Copy project files
COPY . .

# Fix line endings in entrypoint.sh
RUN sed -i 's/\r$//' entrypoint.sh

# Generate certificates
RUN python generate_cert.py

# Copy entrypoint script and make it executable
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose port 8000
EXPOSE 8000

# Start command
CMD ["/bin/bash", "./entrypoint.sh"] 