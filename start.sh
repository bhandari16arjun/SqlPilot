#!/bin/bash
python scripts/index_rag.py &
exec uvicorn app.api:app --host 0.0.0.0 --port $PORT
