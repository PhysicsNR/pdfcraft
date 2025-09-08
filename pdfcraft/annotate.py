
from __future__ import annotations
import fitz  # PyMuPDF

def highlight_text(input_path: str, output_path: str, needle: str) -> int:
    """
    Highlight all occurrences of 'needle' (case-insensitive) in the document.
    """
    hits = 0
    with fitz.open(input_path) as doc:
        for page in doc:
            for inst in page.search_for(needle, flags=fitz.TEXT_DEHYPHENATE | fitz.TEXT_IGNORECASE):
                annot = page.add_highlight_annot(inst)
                hits += 1
        doc.save(output_path, incremental=False, deflate=True)
    return hits

def watermark_text(input_path: str, output_path: str, text: str, opacity: float = 0.15):
    with fitz.open(input_path) as doc:
        for page in doc:
            r = page.rect
            page.insert_text(
                r.tl + (20, 60), text,
                fontsize=48, rotate=45, color=(0, 0, 0), fill_opacity=opacity
            )
        doc.save(output_path, deflate=True)
