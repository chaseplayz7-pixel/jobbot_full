FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure Playwright browsers are installed (image usually includes them,
# but run install to be safe and compatible with local images)
RUN python -m playwright install chromium

ENV PYTHONUNBUFFERED=1

# Default: run the Playwright full scraper. Override command to run tests or
# start the Flask UI as needed.
CMD ["python", "playwright_full.py"]
