# ingestion/converter.py — Docling DocumentConverter factory

from typing import Any

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    PictureDescriptionApiOptions,
    TableFormerMode,
    TableStructureOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

from config import OLLAMA_URL, VLM_MAX_TOKENS, VLM_MODEL, VLM_PROMPT, VLM_TIMEOUT


def _build_picture_description_options() -> PictureDescriptionApiOptions:
    return PictureDescriptionApiOptions(
        url=f"{OLLAMA_URL}/v1/chat/completions",
        params=dict[str, Any](
            model=VLM_MODEL,
            think=False,
            seed=42,
            max_completion_tokens=VLM_MAX_TOKENS,
        ),
        prompt=VLM_PROMPT,
        timeout=VLM_TIMEOUT,
    )


def _build_pdf_pipeline_options() -> PdfPipelineOptions:
    return PdfPipelineOptions(
        enable_remote_services=True,
        do_ocr=False,
        do_table_structure=True,
        generate_picture_images=True,
        do_picture_description=True,
        table_structure_options=TableStructureOptions(
            mode=TableFormerMode.ACCURATE,
        ),
        picture_description_options=_build_picture_description_options(),
    )


def build_converter() -> DocumentConverter:
    """
    Return a DocumentConverter configured with rich PDF options.
    Non-PDF formats use Docling's default pipelines.
    """
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=_build_pdf_pipeline_options(),
                backend=PyPdfiumDocumentBackend,
            )
        }
    )