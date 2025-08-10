from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import List, Optional, Any, Dict
from time import perf_counter
from pathlib import Path
import json
import yaml

from ..validation.invoice_request_validation import validate_request
from ...modules.pdf_reader.pdf_reader import PDFReader
from ...modules.processing_core.processor import ProcessingService

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _load_config() -> dict:
    """
    Carga el fichero YAML de configuración desde backend/config/config.yml.
    """
    cfg_path = Path(__file__).resolve().parents[3] / "config" / "config.yml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@router.post("/process-pdf")
async def process_pdf(
    files: List[UploadFile] = File(..., description="Lista de archivos PDF"),
    asesoria: str = Form(..., description="Nombre de la asesoría"),
    forzarOCR: Optional[bool] = Form(False, description="Forzar OCR"),
    opciones: Optional[str] = Form(None, description="Opciones adicionales en JSON"),
) -> Any:
    """
    Endpoint que procesa uno o más archivos PDF y devuelve los datos extraídos.
    Valida la solicitud, lee cada PDF, selecciona la plantilla, extrae campos y calcula confianza.
    """
    started = perf_counter()
    config = _load_config()

    # Convertir opciones JSON en diccionario
    opciones_dict: Dict[str, Any] = {}
    if opciones:
        try:
            opciones_dict = json.loads(opciones)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"field": "opciones", "error": "Debe ser JSON válido"}],
            )

    # Validar la solicitud
    try:
        validate_request(
            files=files,
            asesoria=asesoria,
            forzar_ocr=bool(forzarOCR),
            opciones=opciones_dict,
            config=config,
        )
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))

    reader = PDFReader(config=config)
    processor = ProcessingService(
        config=config,
        templates_dir=str(Path(__file__).resolve().parents[3] / "templates"),
    )

    results: List[Dict[str, Any]] = []
    for up_file in files:
        pdf_bytes = await up_file.read()
        read_obj = reader.read(
            pdf_bytes=pdf_bytes,
            force_ocr=bool(forzarOCR),
            filename=up_file.filename,
        )
        processed = processor.process(
            read_obj=read_obj,
            asesoria=asesoria,
            filename=up_file.filename,
        )
        processed["processing_ms"] = int((perf_counter() - started) * 1000)
        results.append(processed)

    return results
