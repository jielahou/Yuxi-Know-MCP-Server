FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY client.py server_sse.py ./

# Expose the default SSE port
EXPOSE 8000

# Run the SSE server
CMD ["python", "server_sse.py"]
