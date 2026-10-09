# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies (required for scikit-learn, building wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 5000

# Command to run the application using Gunicorn for production
# Assuming run.py handles the development server, but for prod we'll use gunicorn
# Wait, let's use the builtin flask dev server just to ensure compatibility with our specific setup if gunicorn isn't in requirements.
# The user wants "peak perfection" so let's add gunicorn
RUN pip install gunicorn

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "run:app"]
