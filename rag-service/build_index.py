from config import (
    BASE,
    EMBED_MODEL,
    DB_PATH,
    COLLECTION,
    BATCH_SIZE,
    CHUNK_SIZE,
    OVERLAP,
)
import chromadb
from store import VectorStore
from document_loader import DocumentLoader

chunks = DocumentLoader(BASE / "data", CHUNK_SIZE, OVERLAP).load()
print(f"Loaded {len(chunks)} chunks")

store = VectorStore(DB_PATH, COLLECTION, EMBED_MODEL, BATCH_SIZE)
total = store.rebuild(chunks)

collection = chromadb.PersistentClient(path=str(DB_PATH)).get_collection(COLLECTION)
print(collection.get(limit=2, include=["metadatas"])["metadatas"])

print(f"Done. The collection has {total} chunks.")