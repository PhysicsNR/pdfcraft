
from __future__ import annotations
from pathlib import Path
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

def ocr_pdf(input_path: str, output_path: str, dpi: int = 300, lang: str = "eng") -> None:
    """
    Render each page to an image, OCR with Tesseract, and stitch back into a searchable PDF.
    """
    out = fitz.open()
    with fitz.open(input_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)  # render
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
            p = fitz.open(stream=pdf_bytes, filetype="pdf")
            out.insert_pdf(p)
            p.close()
    out.save(output_path, deflate=True)
    out.close()
