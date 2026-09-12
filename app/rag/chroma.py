import os
import sqlite3
import chromadb
from chromadb.utils import embedding_functions

# Use a fast, free local embedding model that doesn't require API calls
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

class RAGController:
    def __init__(self, db_dir="data/chroma_db"):
        # Persistent storage for our vectors
        self.client = chromadb.PersistentClient(path=db_dir)
        self.schema_collection = self.client.get_or_create_collection(
            name="schema_chunks", 
            embedding_function=emb_fn
        )
        self.kb_collection = self.client.get_or_create_collection(
            name="business_rules", 
            embedding_function=emb_fn
        )
        self.example_collection = self.client.get_or_create_collection(
            name="golden_examples", 
            embedding_function=emb_fn
        )

    def index_schema(self, sqlite_db_path="data/demo.db"):
        print("Indexing database schema...")
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for (table_name,) in tables:
            # Introspect columns for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_strings = [f"{col[1]} ({col[2]})" for col in columns]
            
            # Format the chunk
            doc = f"Table: {table_name}\nColumns: {', '.join(col_strings)}"
            
            self.schema_collection.upsert(
                documents=[doc],
                metadatas=[{"table": table_name, "type": "schema"}],
                ids=[f"schema_{table_name}"]
            )
        conn.close()
        print(f"Successfully indexed {len(tables)} tables.")

    def index_knowledge_base(self, kb_dir="knowledge_base"):
        print("Indexing business rules...")
        count = 0
        for filename in os.listdir(kb_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(kb_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                rule_id = filename.replace(".md", "")
                
                self.kb_collection.upsert(
                    documents=[content],
                    metadatas=[{"rule": rule_id, "type": "business_rule"}],
                    ids=[f"kb_{rule_id}"]
                )
                count += 1
        print(f"Successfully indexed {count} business rules.")

    def index_examples(self, examples_path="data/examples.json"):
        import json
        print("Indexing golden examples...")
        if not os.path.exists(examples_path):
            print("No examples.json found, skipping.")
            return
            
        with open(examples_path, 'r', encoding='utf-8') as f:
            examples = json.load(f)
            
        count = 0
        for i, ex in enumerate(examples):
            doc = f"Question: {ex['question']}\nSQL: {ex['sql']}"
            self.example_collection.upsert(
                documents=[doc],
                metadatas=[{"type": "example"}],
                ids=[f"example_{i}"]
            )
            count += 1
        print(f"Successfully indexed {count} examples.")

    def retrieve_context(self, question: str, n_schema=4, n_kb=2, n_examples=2) -> str:
        """Searches ChromaDB for the most relevant tables, rules, and examples."""
        
        # Search for tables
        schema_results = self.schema_collection.query(
            query_texts=[question],
            n_results=n_schema
        )
        
        # Search for business logic
        kb_results = self.kb_collection.query(
            query_texts=[question],
            n_results=n_kb
        )
        
        # Search for golden examples
        example_results = self.example_collection.query(
            query_texts=[question],
            n_results=n_examples
        )
        
        context_parts = []
        context_parts.append("=== RELEVANT DATABASE TABLES ===")
        if schema_results['documents'] and len(schema_results['documents'][0]) > 0:
            for doc in schema_results['documents'][0]:
                context_parts.append(doc)
        
        context_parts.append("\n=== RELEVANT BUSINESS RULES ===")
        if kb_results['documents'] and len(kb_results['documents'][0]) > 0:
            for doc, distance in zip(kb_results['documents'][0], kb_results['distances'][0]):
                if distance < 1.6:  
                    context_parts.append(doc)
                    
        context_parts.append("\n=== RELEVANT GOLDEN SQL EXAMPLES ===")
        if example_results['documents'] and len(example_results['documents'][0]) > 0:
            for doc, distance in zip(example_results['documents'][0], example_results['distances'][0]):
                if distance < 1.5:  
                    context_parts.append(doc)
                    
        return "\n\n".join(context_parts)
