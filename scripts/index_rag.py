import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.rag.chroma import RAGController

def main():
    try:
        print("Starting RAG Indexing Pipeline...")
        rag = RAGController()
        rag.index_schema()
        rag.index_knowledge_base()
        rag.index_examples()
        print("Done! ChromaDB is now populated.")
    except Exception as e:
        print(f"CRITICAL WARNING: RAG Indexing failed on boot: {e}")
        traceback.print_exc()
        print("Continuing boot sequence anyway so Uvicorn doesn't crash...")

if __name__ == "__main__":
    main()
