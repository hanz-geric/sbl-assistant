from pathlib import Path

BASE = Path(__file__).parent

# llm
CHAT_MODEL = "gpt-oss:120b-cloud"
N_RESULTS = 5
MAX_DISTANCE = 1.0

# Generation settings
TEMPERATURE = 0.2
TOP_P = 0.9
NUM_CTX = 8192
MAX_TOKENS = 1024

SYSTEM_PROMPT = """You help people in Baguio City and Benguet start and run small businesses.

Answer using ONLY the context provided. Rules:
- If the context does not contain the answer, say you don't have that information and suggest contacting the relevant office. Never guess fees, amounts, or deadlines.
- Information marked FOR VALIDATION or INTERVIEW-DERIVED is not fully verified. Say so when you rely on it.
- Keep answers short and practical.
- Reply in the same language the user wrote in.
"""

NO_ANSWER = (
    "I don't have information about that. "
    "Please ask the DTI Baguio–Benguet office or a Negosyo Center."
)

# document loader
CHUNK_SIZE = 800
OVERLAP = 100

# vector store
EMBED_MODEL = "bge-m3"
DB_PATH = BASE / "chroma_db"
COLLECTION = "knowledge_base"
BATCH_SIZE = 12