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
    # OpenGL fix ONLY
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Utilities
    curl \
    # COMPILATION DEPENDENCIES
    build-essential \
    libyaml-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Install ONLY opencv-python-headless
RUN uv pip install opencv-python-headless

# Copy application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]