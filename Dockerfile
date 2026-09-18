FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for compiling certain python packages like ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (data/demo.db is now included via .dockerignore fix)
COPY . .

# Create directory for ChromaDB vectors (generated at runtime)
RUN mkdir -p /app/data

# Expose the default port Render uses
EXPOSE 10000

# Seed the database at build time so it's baked into the image
RUN python scripts/seed_database.py

# Default command - render.yaml overrides this with the full startup sequence
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "10000"]
