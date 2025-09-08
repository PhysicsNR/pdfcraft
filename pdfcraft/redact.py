
from __future__ import annotations
import fitz  # PyMuPDF

def redact_text(input_path: str, output_path: str, needle: str) -> int:
    """
    Find text occurrences and apply vector redaction (not just draw a box).
    """
    hits = 0
    with fitz.open(input_path) as doc:
        for page in doc:
            rects = page.search_for(needle, flags=fitz.TEXT_DEHYPHENATE | fitz.TEXT_IGNORECASE)
            for r in rects:
                page.add_redact_annot(r, fill=(0, 0, 0))
                hits += 1
            if rects:
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        doc.save(output_path, deflate=True)
    return hits
