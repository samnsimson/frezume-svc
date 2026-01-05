FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # WeasyPrint dependencies
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    # Database/XML
    libpq5 \
    libxml2 \
    libxslt1.1 \
    # Fonts
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-cjk \
    # Utilities
    curl \
    # COMPILATION DEPENDENCIES (CRITICAL)
    build-essential \
    libyaml-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]