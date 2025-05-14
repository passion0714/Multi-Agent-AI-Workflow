FROM python:3.9-slim

ARG SERVICE=all

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright/browser dependencies if this is the data entry agent
RUN if [ "$SERVICE" = "data_entry_agent" ] || [ "$SERVICE" = "all" ]; then \
    apt-get update && apt-get install -y \
    libwoff1 \
    libopus0 \
    libwebp6 \
    libwebpdemux2 \
    libenchant1c2a \
    libgudev-1.0-0 \
    libsecret-1-0 \
    libhyphen0 \
    libgdk-pixbuf2.0-0 \
    libegl1 \
    libnotify4 \
    libxslt1.1 \
    libevent-2.1-7 \
    libgles2 \
    libvpx5 \
    libxcomposite1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libepoxy0 \
    libgtk-3-0 \
    libharfbuzz-icu0 \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-libav \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* ; \
    fi

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers if this is the data entry agent
RUN if [ "$SERVICE" = "data_entry_agent" ] || [ "$SERVICE" = "all" ]; then \
    playwright install chromium \
    && playwright install-deps chromium ; \
    fi

# Copy the entire project
COPY . .

# Create volume directories
RUN mkdir -p /app/shared/logs

# Set environment variable for Python path
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "-m", "shared.api"] 