# config.py — centralised settings and constants

import os
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Vision-language model used for picture descriptions
VLM_MODEL = "qwen3-vl:2b"
VLM_PROMPT = (
    "Tu es un spécialiste de l'OCR. "
    "Extrais TOUT le texte visible dans cette image, de haut en bas, de gauche à droite. "
)

# Text model used for chat
CHAT_MODEL = "qwen2.5:7b"
ENABLE_CACHE = True
# Embedding model
EMBED_MODEL = "nomic-embed-text:latest"

# Markdown export markers
PAGE_BREAK_PLACEHOLDER = "<!-- page_break -->"
IMAGE_DESCRIPTION_START = "<image_description>"
IMAGE_DESCRIPTION_END = "</image_description>"

# FAISS
FAISS_INDEX_NAME = "main_index"

# File types accepted by the Streamlit uploader
SUPPORTED_EXTENSIONS = [
    "pdf", "docx", "pptx", "xlsx",
    "html", "md", "txt",
    "png", "jpg", "jpeg",
]

# Chunking
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400
CHUNK_THRESHOLD = 4000  # docs smaller than this are kept as a single chunk

# Retrieval
RETRIEVER_K = 4

# Embedding
EMBED_TIMEOUT = 60
EMBED_RETRIES = 3
EMBED_RETRY_SLEEP = 5
EMBED_DOC_SLEEP = 1.5        # pause between consecutive embed calls
VLM_TIMEOUT = 90
VLM_MAX_TOKENS = 256