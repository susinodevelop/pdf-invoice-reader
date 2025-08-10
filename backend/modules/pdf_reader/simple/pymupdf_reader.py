"""
Simple text PDF reader using PyMuPDF (fitz).
"""

from typing import Tuple, List, Dict

try:
    import fitz  # type: ignore[attr-defined]
except Exception:
    fitz = None  # type: ignore


class PyMuPDFReader:
    """Extract text from PDF using PyMuPDF for simple text PDFs."""

    def read(self, pdf_file: str) -> Tuple[str, List[Dict[str, object]]]:
        """Read a PDF file and return full text and text blocks.

        Args:
            pdf_file: Path to a PDF file.

        Returns:
            A tuple containing the full extracted text and a list of blocks.
        """
        full_text = ""
        blocks: List[Dict[str, object]] = []
        if fitz is None:
            # If dependency is missing, return empty results
            return full_text, blocks
        with fitz.open(pdf_file) as doc:
            for page in doc:
                # Append full text
                full_text += page.get_text() + "\n"
                # Extract block information: (x0, y0, x1, y1, text, block_no, block_type)
                for block in page.get_text("blocks"):
                    x0, y0, x1, y1, block_text, *_ = block
                    blocks.append({"bbox": (x0, y0, x1, y1), "text": block_text})
        return full_text, blocks
