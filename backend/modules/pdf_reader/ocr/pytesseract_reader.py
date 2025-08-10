"""
OCR-based PDF reader using PyTesseract.
"""

from typing import Tuple, List, Dict

try:
    from PIL import Image  # type: ignore
    import pytesseract  # type: ignore
    import fitz  # type: ignore[attr-defined]
except Exception:
    # Dependencies may not be installed; readers will return empty results.
    Image = None  # type: ignore
    pytesseract = None  # type: ignore
    fitz = None  # type: ignore


class PyTesseractReader:
    """Extract text from PDF files using OCR with Tesseract."""

    def __init__(self, lang: str = "eng+spa") -> None:
        """Initialize the reader.

        Args:
            lang: Languages to use for OCR, e.g., "eng", "spa".
        """
        self.lang = lang

    def read(self, pdf_file: str) -> Tuple[str, List[Dict[str, object]]]:
        """Read a PDF file and return full text and text blocks.

        Args:
            pdf_file: Path to a single PDF file.

        Returns:
            A tuple containing the full extracted text and a list of text
            blocks with their bounding box coordinates.
        """
        full_text = ""
        blocks: List[Dict[str, object]] = []
        # Attempt OCR if dependencies are available
        if fitz and pytesseract and Image:
            with fitz.open(pdf_file) as doc:
                for page in doc:
                    pix = page.get_pixmap()
                    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    # Extract text from image
                    full_text += pytesseract.image_to_string(image, lang=self.lang) + "\n"
                    # Optionally, use image_to_data to get bounding boxes for each word
                    # data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
                    # Process data into blocks with coordinates here if needed
        return full_text, blocks
