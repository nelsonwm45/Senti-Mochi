FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (already included in the base image)
RUN playwright install chromium

# Copy app
COPY . .

# Expose port
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
