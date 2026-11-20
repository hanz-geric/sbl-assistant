
import ollama

from config import (
    CHAT_MODEL,
    MAX_DISTANCE,
    MAX_TOKENS,
    N_RESULTS,
    NO_ANSWER,
    NUM_CTX,
    SYSTEM_PROMPT,
    TEMPERATURE,
    TOP_P,
)

class Assistant:
    def __init__(self, store):
        self.store = store

    def ask(self, question):
        results = self.store.search(question, n_results=N_RESULTS)
        chunks = self.pick_chunks(results)

        if not chunks:
            return {"answer": NO_ANSWER, "sources": []}

        context = "\n\n".join(
            f"[{chunk['id']}] {chunk['title']}\n{chunk['text']}" for chunk in chunks
        )
        response = ollama.chat(
            model = CHAT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            options={
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
                "num_ctx": NUM_CTX,
                "num_predict": MAX_TOKENS,
            },
        )

        return {
            "answer": response["message"]["content"],
            "sources": [
                {"id": chunk["id"], "title": chunk["title"], "source": chunk["source"]}
                for chunk in chunks
            ],
        }

    def pick_chunks(self, results):
        """Keeps only the chunks that are close enough to the question."""
        chunks = []
        for chunk_id, text, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if distance <= MAX_DISTANCE:
                chunks.append({
                    "id": chunk_id,
                    "text": text,
                    "title": metadata["title"],
                    "source": metadata.get("source", ""),
                })
        return chunks