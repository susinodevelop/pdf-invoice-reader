"""
Invoice processing API controller.

This controller exposes a single endpoint that accepts one or more PDF
files along with some parameters describing how the PDFs should be
processed. In this scaffold implementation the endpoint simply
returns a basic structure for each file without performing real
extraction logic. The structure is designed to reflect the expected
shape of a future, more complete implementation.
"""

from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form

router = APIRouter(prefix="", tags=["invoices"])

@router.post("/process-pdf")
async def process_pdf(
    files: List[UploadFile] = File(..., description="One or more PDF files to process"),
    asesoria: str = Form(..., description="Identifier for the client/asesoria"),
    forzarOCR: Optional[bool] = Form(False, description="Force OCR processing")
) -> list:
    """Stub implementation of the PDF processing endpoint.

    For each uploaded file this returns a dictionary with placeholder
    fields and confidence scores. Real extraction and template
    selection logic should be added in future iterations.

    Args:
        files: List of uploaded PDF files.
        asesoria: Name of the asesoria/client.
        forzarOCR: Whether to force OCR processing.

    Returns:
        A list of result dictionaries, one per file.
    """
    results = []
    for uploaded_file in files:
        result = {
            "filename": uploaded_file.filename,
            "asesoria": asesoria,
            "template": "default/default.yml",
            "fields": {
                "issue_date": {"value": None, "confidence": 0.0},
                "issuer": {"value": None, "confidence": 0.0},
                "nif": {"value": None, "confidence": 0.0},
            },
            "overall_confidence": 0.0,
        }
        results.append(result)
    return results
