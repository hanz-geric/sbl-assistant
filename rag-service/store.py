import re
import chromadb
import ollama

class VectorStore:
    def __init__(self, db_path, name, model, batch_size):
        self.client = chromadb.PersistentClient(path = str(db_path))
        self.name = name
        self.model = model
        self.batch_size = batch_size

    def rebuild(self, chunks):
        try:
            self.client.delete_collection(self.name)
        except:
            pass
        collection = self.client.create_collection(self.name)

        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start: start + self.batch_size]
            texts = [chunk["title"] + "\n" + chunk["text"] for chunk in batch]
            vectors = ollama.embed(model = self.model, input = texts)["embeddings"]

            collection.add(
                ids = [chunk["id"] for chunk in batch],
                documents = [chunk["text"] for chunk in batch],
                embeddings = vectors,
                metadatas = [
                    {
                        "section": chunk["section"],
                        "title": chunk["title"],
                        "status": self.get_status(chunk["text"]),
                        "source": chunk.get("source", ""),
                        "source_type": chunk.get("source_type", ""),
                    }
                    for chunk in batch
                ]
            )

            print(f"Saved { start + len(batch) } / { len(chunks) }")

        return collection.count()

    def search(self, question, n_results = 5, where = None):
        collection = self.client.get_collection(self.name)
        vector = ollama.embed(self.model, input = [question])["embeddings"]

        return collection.query(
            query_embeddings = vector,
            n_results = n_results,
            where = where
        )

    @staticmethod
    def get_status(text):
            found = re.findall(r"\(Status: ([^)]*)\)", text)
            return found[-1] if found else ""