#!/bin/bash
# RAG indexing is skipped - the schema fallback reads directly from SQLite
exec uvicorn app.api:app --host 0.0.0.0 --port "$PORT"
