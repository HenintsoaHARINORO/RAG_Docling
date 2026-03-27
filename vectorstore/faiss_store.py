# vectorstore/faiss_store.py — build a FAISS vectorstore from text chunks

from langchain_community.vectorstores import faiss

from embeddings import DirectOllamaEmbeddings


def get_vectorstore(chunks: list[str], source_name: str = "") -> faiss.FAISS:
    """
    Embed *chunks* with Ollama and return a FAISS vectorstore.

    Args:
        chunks:      List of text strings to embed.
        source_name: Optional label stored as ``source`` metadata on every chunk.
    """
    embeddings = DirectOllamaEmbeddings()
    metadatas = [{"source": source_name} for _ in chunks]
    return faiss.FAISS.from_texts(texts=chunks, embedding=embeddings, metadatas=metadatas)