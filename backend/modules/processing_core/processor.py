from __future__ import annotations

from typing import Dict, Any, List
from .template_selector import TemplateSelector
from .field_extractor import FieldExtractor
from .confidence import ConfidenceCalculator
from pathlib import Path


class ProcessingService:
    """
    Servicio principal del 'processing core'.
    Orquesta selección de plantilla, extracción de campos y cálculo de confianza.
    """

    def __init__(self, *, config: Dict[str, Any], templates_dir: str) -> None:
        self.config = config or {}
        self.templates_dir = templates_dir
        self.selector = TemplateSelector(templates_dir)
        self.extractor = FieldExtractor()
        self.confidence = ConfidenceCalculator()

    def process(self, *, read_obj: Dict[str, Any], asesoria: str, filename: str) -> Dict[str, Any]:
        """
        read_obj: salida de PDFReader.read(...)
        """
        full_text: str = read_obj.get("full_text", "") or ""
        # 1) Seleccionar plantilla
        tpl, tpl_path, warnings = self.selector.select_template(asesoria=asesoria, file_name=filename, full_text=full_text)

        # 2) Extraer campos
        fields_result = self.extractor.extract_fields(template=tpl, text=full_text, blocks=self._to_blocks(read_obj))

        # 3) Confianzas por campo y global
        overall = self.confidence.calculate_confidence(extracted=fields_result)

        return {
            "filename": filename,
            "asesoria": asesoria,
            "template": tpl_path,
            "fields": fields_result,
            "overall_confidence": overall,
            "warnings": warnings,
        }

    @staticmethod
    def _to_blocks(read_obj: Dict[str, Any]) -> List[Any]:
        """
        Convierte la salida del reader a una lista simple de bloques (compat con FieldExtractor).
        """
        pages = read_obj.get("pages", []) or []
        out: List[Any] = []
        for p in pages:
            for b in p.get("blocks", []) or []:
                out.append(b)
        return out
