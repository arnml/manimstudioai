# Use the official Manim Community image as base
FROM manimcommunity/manim:latest

# Switch to root user to install system dependencies
USER root

# Install system dependencies for networking and process management
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories as root
RUN mkdir -p /app/media /tmp/manim_temp
RUN chmod -R 777 /tmp/manim_temp
RUN chown -R manimuser:manimuser /app

# Switch back to manimuser
USER manimuser

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

# Add local bin to PATH for installed scripts
ENV PATH="/manim/.local/bin:$PATH"

# Copy the application
COPY main.py main.py

# Expose port (Cloud Run uses PORT environment variable)
EXPOSE 8080

# Run the unified application (Cloud Run sets PORT env var)
CMD python -m uvicorn main:socket_app --host 0.0.0.0 --port ${PORT:-8080}