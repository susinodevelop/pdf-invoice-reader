from __future__ import annotations

"""
Validación de la request de /process-pdf.
"""
import re
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException, status

PDF_MIME_WHITELIST = {"application/pdf"}
ASESORIA_RE = re.compile(r"^[a-z0-9_\-]{2,50}$")


def _config_num(config: dict, path: str, default: int) -> int:
    try:
        cur = config
        for k in path.split("."):
            cur = cur[k]
        return int(cur)
    except Exception:
        return default


def validate_request(
    *,
    files: List[UploadFile],
    asesoria: str,
    forzar_ocr: bool,
    opciones: Dict[str, Any],
    config: Dict[str, Any],
) -> None:
    errors = []

    if not files:
        errors.append({"field": "files", "error": "Debes adjuntar al menos un PDF"})

    max_files = _config_num(config, "api.max_files", 25)
    if files and len(files) > max_files:
        errors.append({"field": "files", "error": f"Demasiados archivos. Máximo permitido: {max_files}"})

    # Tipo MIME básico (UploadFile.content_type es indicativo)
    for f in files or ():
        if f.content_type and f.content_type not in PDF_MIME_WHITELIST:
            errors.append({"field": f"files[{f.filename}]", "error": f"Tipo no soportado: {f.content_type}"})

    # asesoria
    if not asesoria or not ASESORIA_RE.match(asesoria):
        errors.append(
            {"field": "asesoria", "error": "Formato inválido. Solo a-z, 0-9, guion y guion_bajo (2..50 caracteres)"}
        )

    # opciones debe ser dict conocido si llega
    if opciones and not isinstance(opciones, dict):
        errors.append({"field": "opciones", "error": "Debe ser un objeto JSON"})

    if errors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors)
