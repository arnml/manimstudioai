FROM manimcommunity/manim:latest

# Switch to root to install packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/media /tmp/manim_temp

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set permissions for tmp directory
RUN chmod -R 777 /tmp/manim_temp

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
