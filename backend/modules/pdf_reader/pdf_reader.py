"""
PDF Reader service module
"""

from typing import List, Dict, Tuple

# Import specific OCR and simple text reader classes
from .ocr.pytesseract_reader import PyTesseractReader
from .simple.pymupdf_reader import PyMuPDFReader


class PDFReader:
    """Facade service for reading PDF files.

    Depending on the force_ocr flag and the ability to extract text
    directly, this service will choose between a simple text extraction
    approach and an OCR approach.
    """

    def __init__(self, force_ocr: bool = False) -> None:
        """Initialize the PDFReader service.

        Args:
            force_ocr: When True, always use OCR even if text extraction
                may be possible via a simple reader.
        """
        self.force_ocr = force_ocr
        self.ocr_reader = PyTesseractReader()
        self.text_reader = PyMuPDFReader()

    def read(self, pdf_files: List[str]) -> Dict[str, Dict[str, object]]:
        """Read a list of PDF files and return their extracted contents.

        Args:
            pdf_files: List of paths to PDF files.

        Returns:
            A dict keyed by file path containing 'text' and 'blocks', where
            'text' is the full extracted text, and 'blocks' is a list of
            text blocks with their bounding box coordinates.
        """
        results: Dict[str, Dict[str, object]] = {}
        for pdf_file in pdf_files:
            # Attempt simple text extraction first unless forced to use OCR
            if not self.force_ocr:
                try:
                    text, blocks = self.text_reader.read(pdf_file)
                except Exception:
                    # Fallback to OCR if simple extraction fails
                    text, blocks = self.ocr_reader.read(pdf_file)
            else:
                # Always use OCR when forced
                text, blocks = self.ocr_reader.read(pdf_file)
            results[pdf_file] = {"text": text, "blocks": blocks}
        return results
