import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
PAPERS_DIR = DATA_DIR / "papers"
INDEXES_DIR = DATA_DIR / "indexes"
SESSIONS_DIR = DATA_DIR / "sessions"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

TOP_K = int(os.getenv("TOP_K", "5"))
QA_MIN_SIMILARITY = float(os.getenv("QA_MIN_SIMILARITY", "0.30"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1400"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "220"))
ARXIV_MAX_RESULTS = int(os.getenv("ARXIV_MAX_RESULTS", "10"))
ARXIV_TIMEOUT = int(os.getenv("ARXIV_TIMEOUT", "30"))

for directory in (PAPERS_DIR, INDEXES_DIR, SESSIONS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
