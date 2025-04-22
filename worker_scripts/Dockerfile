# Use an official Python runtime as the base image
FROM python:3.13.2-bookworm

# Set the working directory
WORKDIR /app

# Copy the application files
COPY worker.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir requests opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# Run the worker script
CMD ["python", "worker.py"]
