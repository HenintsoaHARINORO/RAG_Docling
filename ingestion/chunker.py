# ingestion/chunker.py — split raw Markdown text into overlapping chunks

from langchain.text_splitter import CharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, CHUNK_THRESHOLD


def get_chunks(raw_text: str) -> list[str]:
    """
    Split *raw_text* into overlapping chunks suitable for embedding.

    Documents that fit within ``CHUNK_THRESHOLD`` characters are returned
    as a single chunk to avoid unnecessary fragmentation.
    """
    if len(raw_text) <= CHUNK_THRESHOLD:
        return [raw_text]

    splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    return splitter.split_text(raw_text)