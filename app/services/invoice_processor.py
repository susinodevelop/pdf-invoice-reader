"""Core service logic for processing invoice PDFs.

This module encapsulates the workflow for ingesting a PDF file,
differentiating between embedded text and scanned images, running
optical character recognition as necessary, extracting key fields,
drawing out tabular data and producing a consistent JSON response.

Where possible, the implementation falls back gracefully when
optional dependencies are missing, for example if the OCR engine
isn't available in the runtime environment. Such fallback behaviour
allows the code to be executed in constrained environments while
still exposing the intended API surface.
"""

from __future__ import annotations

import hashlib
import io
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
except ImportError:
    pytesseract = None  # type: ignore
    Image = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ProcessingParams:
    """Container for user-provided processing parameters."""

    language_hint: Optional[str] = None
    return_layout: bool = False
    return_tables: bool = False
    ocr_force: bool = False
    ocr_engine: str = "auto"
    redact_pii: bool = False


class InvoiceProcessor:
    """Class responsible for orchestrating invoice processing."""

    TEXT_THRESHOLD: int = 200  # Minimum characters to consider a page as having native text

    def process_invoice(
        self, file_bytes: bytes, filename: str, params: ProcessingParams
    ) -> Dict[str, Any]:
        """Process a single PDF invoice and produce a structured result.

        :param file_bytes: The raw PDF file content.
        :param filename: Original file name of the uploaded PDF.
        :param params: Processing parameters provided by the API request.
        :return: Structured JSON-like dict containing extraction results.
        """
        logger.debug("Starting processing for %s", filename)
        # Compute hash for identification
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Open the PDF via PyMuPDF
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            logger.error("Failed to open PDF %s: %s", filename, exc)
            raise

        pages_count = doc.page_count
        metadata = self._extract_pdf_metadata(doc)

        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        tables: List[Dict[str, Any]] = []
        images_data: List[Dict[str, Any]] = []
        scanned_ratio_count = 0

        for page_number in range(pages_count):
            page = doc.load_page(page_number)
            logger.debug("Processing page %d", page_number + 1)
            # Determine if we should run OCR
            native_text = page.get_text("text").strip()
            use_ocr = params.ocr_force or len(native_text) < self.TEXT_THRESHOLD
            if use_ocr:
                scanned_ratio_count += 1
                ocr_text, page_images = self._run_ocr_on_page(page, params.language_hint)
                full_text_parts.append(ocr_text)
                if params.return_layout:
                    # We return layout as blocks with bounding boxes for OCR results
                    blocks = [
                        {
                            "text": ocr_text,
                            "coords": [0, 0, 0, 0],  # Without detailed detection we cannot provide real coords
                            "confidence": None,
                        }
                    ]
                else:
                    blocks = []
                page_dict = {
                    "number": page_number + 1,
                    "text": ocr_text,
                    "blocks": blocks,
                }
                pages_data.append(page_dict)
                # Add raw images info if requested
                for idx, img in enumerate(page_images):
                    images_data.append(
                        {
                            "page": page_number + 1,
                            "index": idx,
                            "width": img.width,
                            "height": img.height,
                        }
                    )
            else:
                # Use native text extraction
                full_text_parts.append(native_text)
                if params.return_layout:
                    # Extract blocks and coords
                    blocks = self._extract_text_blocks(page)
                else:
                    blocks = []
                page_dict = {
                    "number": page_number + 1,
                    "text": native_text,
                    "blocks": blocks,
                }
                pages_data.append(page_dict)

            # Table extraction is optional and very simplistic here
            if params.return_tables:
                page_tables = self._extract_tables(page)
                for tbl in page_tables:
                    tbl["page"] = page_number + 1
                    tables.append(tbl)

        # Combine all extracted text
        full_text = "\n".join(full_text_parts)

        # Perform redaction if requested
        if params.redact_pii:
            redacted_text, entities = self._redact_pii(full_text)
        else:
            redacted_text = full_text
            entities = []

        # Infer invoice fields from combined text
        inferred_fields = self._extract_fields(full_text)

        # Diagnostics information
        diagnostics = {
            "pages_count": pages_count,
            "scanned_pages": scanned_ratio_count,
            "ocr_engine_used": "tesseract" if pytesseract else None,
        }

        result: Dict[str, Any] = {
            "file_name": filename,
            "hash_sha256": file_hash,
            "pages_count": pages_count,
            "pdf_properties": metadata,
            "text_full": redacted_text,
            "pages": pages_data,
            "tables": tables,
            "images": images_data,
            "inferred_fields": inferred_fields,
            "diagnostics": diagnostics,
        }
        if params.redact_pii:
            result["entities"] = entities
        return result

    def _extract_pdf_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract metadata and properties from a PyMuPDF document."""
        meta = doc.metadata or {}
        xmp = meta.get("metadata")
        return {
            "producer": meta.get("producer"),
            "creation_date": meta.get("creationDate"),
            "mod_date": meta.get("modDate"),
            "is_encrypted": doc.is_encrypted,
            "has_text": doc.is_textual,
            "xmp_metadata": xmp,
        }

    def _extract_text_blocks(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """Extract text blocks and their coordinates from a page.

        :param page: PyMuPDF page object.
        :return: List of dictionaries with text and bounding box coordinates.
        """
        blocks_out: List[Dict[str, Any]] = []
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text, *_rest = block
            blocks_out.append(
                {
                    "text": text.strip(),
                    "coords": [x0, y0, x1, y1],
                }
            )
        return blocks_out

    def _run_ocr_on_page(
        self, page: fitz.Page, language_hint: Optional[str]
    ) -> (str, List[Image.Image]):
        """Run OCR on a scanned page.

        Converts the page to an image and uses pytesseract to extract text.
        If pytesseract is not available, returns an empty string.

        :param page: PyMuPDF page.
        :param language_hint: Optional language hint to pass to tesseract.
        :return: Tuple of extracted text and list of PIL images representing the page.
        """
        if pytesseract is None or Image is None:
            logger.warning("pytesseract is not available; returning empty OCR result")
            return "", []
        # Render page as image at 200 DPI for better OCR quality
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        lang = language_hint if language_hint else "eng"
        try:
            text = pytesseract.image_to_string(img, lang=lang)
        except Exception as exc:
            logger.error("Failed running OCR: %s", exc)
            text = ""
        return text.strip(), [img]

    def _extract_tables(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """Attempt to extract tables from the given page.

        Currently, this implementation is a placeholder that always returns an empty
        list. To enable table extraction, integrate Camelot or Tabula here.

        :param page: PyMuPDF page.
        :return: List of table dicts.
        """
        # Placeholder; real implementation would use camelot or tabula on the page
        return []

    def _extract_fields(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Extract key invoice fields from the given text.

        This is a simplified heuristic-based extractor. For production use,
        consider using a trained NLP model or rules engine. Each field
        dictionary contains value, confidence and evidence keys.

        :param text: Combined text from all pages.
        :return: Mapping of field names to extracted values and metadata.
        """
        fields: Dict[str, Dict[str, Any]] = {}

        # Helper function to build field dicts
        def make_field(value: Optional[str], confidence: float, evidence: str) -> Dict[str, Any]:
            return {
                "value": value,
                "confidence": confidence,
                "evidence": {"text": evidence, "coords": None},
            }

        # Extract invoice number
        invoice_number = None
        conf_invoice = 0.0
        # Look for patterns like FAC-12345 or Invoice #: 1234
        match = re.search(r"(?:invoice|factura)[:\s#-]*([A-Za-z0-9/.-]+)", text, re.IGNORECASE)
        if match:
            invoice_number = match.group(1).strip()
            conf_invoice = 0.9
        fields["invoice_number"] = make_field(invoice_number, conf_invoice, match.group(0) if match else "")

        # Extract issue date
        date_value = None
        conf_date = 0.0
        date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
        if date_match:
            raw_date = date_match.group(1)
            try:
                # Try multiple formats
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"]:
                    try:
                        dt = datetime.strptime(raw_date, fmt)
                        date_value = dt.strftime("%Y-%m-%d")
                        conf_date = 0.9
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        fields["issue_date"] = make_field(date_value, conf_date, date_match.group(0) if date_match else "")

        # Supplier and customer detection (very naive)
        supplier = None
        customer = None
        conf_supplier = 0.0
        conf_customer = 0.0
        # Use simple heuristics: look for lines containing "NIF" or "CIF"
        for line in text.splitlines():
            if supplier is None and re.search(r"\b(NIF|CIF)\b", line, re.IGNORECASE):
                supplier = line.strip()
                conf_supplier = 0.6
            if customer is None and re.search(r"\bcliente\b", line, re.IGNORECASE):
                customer = line.strip()
                conf_customer = 0.6
        fields["supplier"] = make_field(supplier, conf_supplier, supplier or "")
        fields["customer"] = make_field(customer, conf_customer, customer or "")

        # Total amount detection
        total_value = None
        conf_total = 0.0
        total_match = re.search(r"total[:\s]*([0-9]+[,.][0-9]{2})", text, re.IGNORECASE)
        if total_match:
            raw_total = total_match.group(1)
            # Normalize decimal comma to dot
            raw_clean = raw_total.replace(",", ".")
            total_value = raw_clean
            conf_total = 0.95
        fields["total"] = make_field(total_value, conf_total, total_match.group(0) if total_match else "")

        # Taxes detection: look for VAT lines
        taxes: List[Dict[str, Any]] = []
        for vat_match in re.finditer(r"(\d{1,2})%\s*(\d+[,.]\d{2})", text):
            rate = vat_match.group(1)
            amount = vat_match.group(2).replace(",", ".")
            taxes.append({"type": f"{rate}%", "amount": amount})
        fields["taxes"] = make_field(taxes if taxes else None, 0.7 if taxes else 0.0, str(taxes))

        # Products: not implemented here
        fields["products"] = make_field(None, 0.0, "")

        return fields

    def _redact_pii(self, text: str) -> (str, List[Dict[str, Any]]):
        """Redact personally identifiable information from text.

        Identifies email addresses, phone numbers and IBANs using
        regular expressions and replaces them with ***. Returns the
        redacted text and a list of the original entities found.
        """
        entities: List[Dict[str, Any]] = []
        # Patterns for email, phone and IBAN
        patterns = {
            "email": re.compile(r"[\w\.]+@[\w\.]+", re.IGNORECASE),
            "phone": re.compile(r"\+?\d[\d\s]{7,}\d"),
            "iban": re.compile(r"[A-Z]{2}\d{2}[A-Z0-9]{1,30}", re.IGNORECASE),
        }
        redacted_text = text
        for kind, pat in patterns.items():
            for match in pat.finditer(text):
                value = match.group(0)
                entities.append({"type": kind, "value": value})
                redacted_text = redacted_text.replace(value, "***")
        return redacted_text, entities
