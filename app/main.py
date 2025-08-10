"""Main module for the Invoice Reader REST API.

This module defines the FastAPI application, sets up the API
endpoints and delegates processing of uploaded PDF invoices to
the underlying service layer.
"""

import hashlib
import logging
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST

from .services.invoice_processor import InvoiceProcessor, ProcessingParams


# Configure basic logging. In a real application you might want
# to configure structured JSON logging and more granular log levels.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Invoice Reader API",
    description="API for ingesting PDF invoices and extracting structured data.",
    version="0.1.0",
)


@app.get("/health", summary="Return API health status")
def health_check() -> JSONResponse:
    """Simple health check endpoint.

    Returns a JSON object indicating that the service is running.
    """
    return JSONResponse({"status": "ok"})


@app.get("/version", summary="Return API version")
def version() -> JSONResponse:
    """Return current API version.

    Reads the version string from the application metadata.
    """
    return JSONResponse({"version": app.version})


@app.post(
    "/ingest",
    summary="Ingest one or more PDF invoices",
    response_description="Structured extraction results for each PDF",
)
async def ingest(
    files: List[UploadFile] = File(..., description="One or more PDF files to process"),
    language_hint: Optional[str] = Query(
        None,
        regex="^(es|gl|en)$",
        description="Optional hint for the OCR language (es, gl, en)",
    ),
    return_layout: bool = Query(
        False, description="Include detailed page layout and bounding boxes in the response"
    ),
    return_tables: bool = Query(
        False, description="Include tables extracted from pages where possible"
    ),
    ocr_force: bool = Query(
        False, description="Force OCR even when the PDF contains embedded text"
    ),
    ocr_engine: str = Query(
        "auto", description="Select OCR engine: tesseract, paddle or auto"
    ),
    redact_pii: bool = Query(
        False, description="Redact personally identifiable information in the extracted text"
    ),
) -> JSONResponse:
    """Handle the ingestion of uploaded PDF files.

    This endpoint accepts one or more PDF files through a multipart/form-data
    request, processes each file according to the provided parameters and
    returns a list of structured extraction results.

    :param files: Uploaded PDF files.
    :param language_hint: Optional ISO language code hint for OCR.
    :param return_layout: Whether to return detailed layout information.
    :param return_tables: Whether to attempt table extraction.
    :param ocr_force: Always run OCR regardless of embedded text.
    :param ocr_engine: Preferred OCR engine (tesseract, paddle, auto).
    :param redact_pii: Whether to redact emails, phones and IBANs from the text.
    :return: JSONResponse containing a list of results per input file.
    """
    logger.info("Received %d file(s) for ingestion", len(files))

    # Validate that at least one file was provided
    if not files:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="No files were provided for ingestion",
        )

    processor = InvoiceProcessor()
    params = ProcessingParams(
        language_hint=language_hint,
        return_layout=return_layout,
        return_tables=return_tables,
        ocr_force=ocr_force,
        ocr_engine=ocr_engine,
        redact_pii=redact_pii,
    )

    results = []
    for upload in files:
        content = await upload.read()
        if upload.content_type not in {"application/pdf", "application/octet-stream"}:
            # Reject files that are not PDFs
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type {upload.content_type} for file {upload.filename}",
            )
        try:
            result = processor.process_invoice(content, upload.filename, params)
            results.append(result)
        except Exception as exc:
            logger.exception("Error processing %s: %s", upload.filename, exc)
            results.append(
                {
                    "file_name": upload.filename,
                    "error": str(exc),
                }
            )

    return JSONResponse(results)
