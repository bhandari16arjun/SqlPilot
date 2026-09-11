import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.rag.chroma import RAGController

def main():
    print("Starting RAG Indexing Pipeline...")
    rag = RAGController()
    rag.index_schema()
    rag.index_knowledge_base()
    print("Done! ChromaDB is now populated.")

if __name__ == "__main__":
    main()
