from assistant import Assistant
from config import BATCH_SIZE, COLLECTION, DB_PATH, EMBED_MODEL
from store import VectorStore

assistant = Assistant(VectorStore(DB_PATH, COLLECTION, EMBED_MODEL, BATCH_SIZE))

print("Ask a question about starting a business (type 'quit' to exit).")

while True:
    try:
        question = input("\nYou: ").strip()
    except (KeyboardInterrupt, EOFError):
        break

    if question.lower() in ("quit", "exit", "q"):
        break
    if not question:
        continue

    try:
        result = assistant.ask(question)
    except Exception as error:
        print(f"Error: {error}")
        continue

    print(f"\nBot: {result['answer']}")
    if result["sources"]:
        print("Sources:", ", ".join(source["id"] for source in result["sources"]))

print("Bye!")