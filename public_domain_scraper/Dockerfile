# Use a lightweight Python base image
FROM python:3.9-slim

# Install system dependencies if you need them, e.g. build-essential, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# You no longer need gutenbergpy if you’re only using requests + bs4
RUN pip install --no-cache-dir requests beautifulsoup4

# Create a working directory
WORKDIR /app

# Copy your script into the container
COPY gutenberg_scrape.py /app/

# By default, run your script
CMD ["python", "gutenberg_scrape.py"]