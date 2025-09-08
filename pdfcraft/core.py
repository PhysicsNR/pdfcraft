
from __future__ import annotations
import fitz  # PyMuPDF
from typing import List, Tuple, Optional
from pathlib import Path
from .utils import parse_page_ranges

def info(path: str) -> dict:
    doc = fitz.open(path)
    md = doc.metadata or {}
    return {
        "path": str(Path(path).resolve()),
        "pages": doc.page_count,
        "is_encrypted": doc.is_encrypted,
        "metadata": md,
        "toc_len": len(doc.get_toc(False))
    }

def merge_pdfs(inputs: List[str], output: str) -> None:
    out = fitz.open()
    for p in inputs:
        with fitz.open(p) as d:
            out.insert_pdf(d)
    out.save(output, deflate=True)

def split_pdf(input_path: str, ranges: str, output_dir: str) -> List[str]:
    out_files = []
    with fitz.open(input_path) as doc:
        pages = parse_page_ranges(ranges, doc.page_count)
        output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
        for i, pg in enumerate(pages, start=1):
            out = fitz.open()
            out.insert_pdf(doc, from_page=pg, to_page=pg)
            out_file = output_dir / f"page_{pg+1:04d}.pdf"
            out.save(out_file, deflate=True)
            out.close()
            out_files.append(str(out_file))
    return out_files

def rotate_pages(input_path: str, output_path: str, pages: str, angle: int) -> None:
    with fitz.open(input_path) as doc:
        targets = parse_page_ranges(pages, doc.page_count)
        for pg in targets:
            page = doc.load_page(pg)
            page.set_rotation((page.rotation + angle) % 360)
        doc.save(output_path, deflate=True)

def extract_text(input_path: str, output_txt: str) -> None:
    with fitz.open(input_path) as doc:
        chunks = []
        for i, page in enumerate(doc, start=1):
            chunks.append(f"----- Page {i} -----\n")
            chunks.append(page.get_text("text"))
        Path(output_txt).write_text("".join(chunks), encoding="utf-8")

def extract_images(input_path: str, output_dir: str) -> int:
    from PIL import Image
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    count = 0
    with fitz.open(input_path) as doc:
        for i, page in enumerate(doc, start=1):
            for img in page.get_images(full=True):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.alpha:  # handle transparent images
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                out = Path(output_dir)/f"p{i:04d}_img{xref}.png"
                pix.save(out)
                count += 1
    return count
