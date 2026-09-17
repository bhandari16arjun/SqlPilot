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

# Copy application code
COPY . .

# Create directories for persistent SQLite data and ChromaDB vectors
RUN mkdir -p /app/data /app/chroma_db

# We leave the command empty because docker-compose will override it 
# to run either the FastAPI server or the Streamlit UI.
