# ingestion/extractor.py — extract Markdown text from uploaded files via Docling

import logging
import os
import tempfile
from pathlib import Path

import streamlit as st
from docling_core.types.doc import ImageRefMode

from config import IMAGE_DESCRIPTION_END, IMAGE_DESCRIPTION_START, PAGE_BREAK_PLACEHOLDER
from ingestion.converter import build_converter

logger = logging.getLogger(__name__)


def get_documents_text(uploaded_files) -> list[tuple[str, bytes, str]]:
    """
    Extract text (as Markdown) from a list of Streamlit UploadedFile objects.

    Supported formats: PDF, DOCX, PPTX, XLSX, HTML, Markdown, plain text,
    PNG, JPEG.

    Returns:
        A list of ``(filename, file_bytes, markdown_text)`` tuples.
        Files that fail to convert are skipped with a sidebar error.
    """
    converter = build_converter()
    results: list[tuple[str, bytes, str]] = []

    for uploaded_file in uploaded_files:
        file_bytes = uploaded_file.read()
        suffix = Path(uploaded_file.name).suffix.lower() or ".bin"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            result = converter.convert(tmp_path)
            raw_markdown = result.document.export_to_markdown(
                image_mode=ImageRefMode.PLACEHOLDER,
                image_placeholder="",
                page_break_placeholder=PAGE_BREAK_PLACEHOLDER,
                include_annotations=True,
                mark_annotations=True,
            )
            # Normalise Docling annotation tags to friendlier markers
            raw_markdown = raw_markdown.replace(
                '<!--<annotation kind="description">-->', IMAGE_DESCRIPTION_START
            )
            raw_markdown = raw_markdown.replace(
                "<!--</annotation>-->", IMAGE_DESCRIPTION_END
            )
        except Exception as exc:
            logger.error("Failed to convert '%s': %s", uploaded_file.name, exc)
            st.sidebar.error(f"Could not process '{uploaded_file.name}': {exc}")
            continue
        finally:
            os.unlink(tmp_path)

        results.append((uploaded_file.name, file_bytes, raw_markdown))

    return results