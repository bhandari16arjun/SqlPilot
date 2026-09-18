import os
import sqlite3
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import create_engine, inspect


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "missing_api_key_prevent_crash_on_boot")
        self.embedder = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_key=api_key
        )

    def __call__(self, input: Documents) -> Embeddings:
        return self.embedder.embed_documents(input)


class RAGController:
    def __init__(self, db_dir="data/chroma_db"):
        # Lazily create the embedding function only when needed
        self._emb_fn = None
        self._db_dir = db_dir
        self._client = None
        self._schema_collection = None
        self._kb_collection = None
        self._example_collection = None

    def _ensure_initialized(self):
        """Lazy initialization to prevent crashing on import when API key is absent."""
        if self._client is not None:
            return
        self._emb_fn = GeminiEmbeddingFunction()
        self._client = chromadb.PersistentClient(path=self._db_dir)
        self._schema_collection = self._client.get_or_create_collection(
            name="schema_chunks",
            embedding_function=self._emb_fn
        )
        self._kb_collection = self._client.get_or_create_collection(
            name="business_rules",
            embedding_function=self._emb_fn
        )
        self._example_collection = self._client.get_or_create_collection(
            name="golden_examples",
            embedding_function=self._emb_fn
        )

    def index_schema(self, sqlite_db_path="data/demo.db"):
        self._ensure_initialized()
        print("Indexing database schema (Batched)...")
        db_url = os.getenv("DATABASE_URL")
        docs, metas, ids = [], [], []

        if db_url and db_url.startswith("postgres"):
            engine = create_engine(db_url)
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                col_strings = [f"{col['name']} ({col['type']})" for col in columns]
                docs.append(f"Table: {table_name}\nColumns: {', '.join(col_strings)}")
                metas.append({"table": table_name, "type": "schema"})
                ids.append(f"schema_{table_name}")
            print(f"Successfully fetched {len(tables)} tables from PostgreSQL.")
        else:
            conn = sqlite3.connect(sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                col_strings = [f"{col[1]} ({col[2]})" for col in columns]
                docs.append(f"Table: {table_name}\nColumns: {', '.join(col_strings)}")
                metas.append({"table": table_name, "type": "schema"})
                ids.append(f"schema_{table_name}")
            conn.close()
            print(f"Successfully fetched {len(tables)} tables from SQLite.")

        if docs:
            self._schema_collection.upsert(documents=docs, metadatas=metas, ids=ids)

    def index_knowledge_base(self, kb_dir="knowledge_base"):
        self._ensure_initialized()
        print("Indexing business rules (Batched)...")
        docs, metas, ids = [], [], []
        if not os.path.exists(kb_dir):
            return
        for filename in os.listdir(kb_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(kb_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    docs.append(f.read())
                rule_id = filename.replace(".md", "")
                metas.append({"rule": rule_id, "type": "business_rule"})
                ids.append(f"kb_{rule_id}")
        if docs:
            self._kb_collection.upsert(documents=docs, metadatas=metas, ids=ids)
        print(f"Successfully indexed {len(docs)} business rules.")

    def index_examples(self, examples_path="data/examples.json"):
        import json
        self._ensure_initialized()
        print("Indexing golden examples (Batched)...")
        docs, metas, ids = [], [], []
        if not os.path.exists(examples_path):
            return
        with open(examples_path, 'r', encoding='utf-8') as f:
            examples = json.load(f)
        for i, ex in enumerate(examples):
            docs.append(f"Question: {ex['question']}\nSQL: {ex['sql']}")
            metas.append({"type": "example"})
            ids.append(f"example_{i}")
        if docs:
            self._example_collection.upsert(documents=docs, metadatas=metas, ids=ids)
        print(f"Successfully indexed {len(docs)} examples.")

    def retrieve_context(self, question: str, n_schema=4, n_kb=2, n_examples=2) -> str:
        self._ensure_initialized()
        schema_results = self._schema_collection.query(query_texts=[question], n_results=n_schema)
        kb_results = self._kb_collection.query(query_texts=[question], n_results=n_kb)
        example_results = self._example_collection.query(query_texts=[question], n_results=n_examples)

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
