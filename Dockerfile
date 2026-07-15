# Use the official lightweight Python image.
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
# Strip out windows-specific requirements before installing
RUN python -c "import sys; lines = [l for l in open('requirements.txt') if not any(w in l.lower() for w in ['pywin32', 'pyautogui', 'pygetwindow', 'keyboard', 'pyrect', 'pyscreeze', 'mouseinfo', 'pytweening', 'xlib'])]; open('requirements_deploy.txt', 'w').write(''.join(lines))" \
    && pip install --no-cache-dir -r requirements_deploy.txt

# Copy project files
COPY . /app/

# Expose port
EXPOSE 8080

# Run the web server using gunicorn
CMD exec gunicorn kitcheniq.wsgi:application --bind 0.0.0.0:${PORT} --workers 3
