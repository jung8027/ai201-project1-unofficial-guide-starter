import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"

# --- Embeddings ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Vector store ---
CHROMA_COLLECTION = "nyu_business_reviews"
CHROMA_PATH = "./chroma_db"

# --- Retrieval ---
N_RESULTS = 5

# Cosine distance ceiling for a chunk to be passed to the LLM.
# all-MiniLM-L6-v2 cosine distances: <0.3 strong, 0.3-0.5 moderate, >0.6 weak.
# 0.75 keeps genuinely relevant review passages while dropping clear misses.
RELEVANCE_THRESHOLD = 0.75

# --- Documents ---
DOCS_PATH = "./documents"
