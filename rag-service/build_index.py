import json
import re
from pathlib import Path

import ollama
import chromadb

BASE = Path(__file__).parent
EMBED_MODEL = "bge-m3"
DB_PATH = BASE / "chroma_db"
COLLECTION = "knowledge_base"
BATCH_SIZE = 12


def get_status(text):
    found = re.findall(r"\(Status: ([^)]*)\)", text)
    return found[-1] if found else ""


with open(BASE / "data" / "chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)
print(f"Loaded {len(chunks)} chunks")

client = chromadb.PersistentClient(path=str(DB_PATH))

try:
    client.delete_collection(COLLECTION)
except Exception:
    pass
collection = client.create_collection(name=COLLECTION)

for start in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[start:start + BATCH_SIZE]

    texts = [c["title"] + "\n" + c["text"] for c in batch]
    vectors = ollama.embed(model=EMBED_MODEL, input=texts)["embeddings"]

    collection.add(
        ids=[c["id"] for c in batch],
        documents=[c["text"] for c in batch],
        embeddings=vectors,
        metadatas=[
            {"section": c["section"], "title": c["title"], "status": get_status(c["text"])}
            for c in batch
        ],
    )
    print(f"Saved {start + len(batch)} / {len(chunks)}")

print(f"Done. The collection has {collection.count()} chunks.")
