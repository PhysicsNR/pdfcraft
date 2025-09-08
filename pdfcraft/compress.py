
from __future__ import annotations
from pathlib import Path
from typing import Optional
from PIL import Image
import io
import pikepdf

def _recompress_images(pdf: pikepdf.Pdf, quality: int = 60, max_dpi: int = 200):
    """
    Recompress embedded images to JPEG/PNG with a max DPI cap.
    Heuristic, safe-ish defaults.
    """
    from pikepdf import PdfImage
    page_index = 0
    for page in pdf.pages:
        page_index += 1
        try:
            images = page.images
        except Exception:
            images = []
        for name, img in images.items():
            try:
                pimg = PdfImage(img)
                pil = pimg.as_pil_image()
                # downscale if DPI suggests over-sized
                dpi = pil.info.get("dpi", (300, 300))[0]
                if dpi > max_dpi:
                    scale = max_dpi / float(dpi)
                    new_size = (max(1, int(pil.width*scale)), max(1, int(pil.height*scale)))
                    pil = pil.resize(new_size)
                # choose JPEG for RGB, PNG fallback for others
                buf = io.BytesIO()
                if pil.mode in ("RGB", "L"):
                    pil.save(buf, format="JPEG", quality=quality, optimize=True)
                    pimg.replace(buf.getvalue(), format="jpeg")
                else:
                    pil.save(buf, format="PNG", optimize=True)
                    pimg.replace(buf.getvalue(), format="png")
            except Exception as e:
                # best-effort: skip unconvertible images
                continue

def compress_pdf(input_path: str, output_path: str, quality: int = 60, max_dpi: int = 200) -> None:
    """
    Best-effort compressor based on image downsampling and recompression.
    Structure/object cleanup is handled by pikepdf on save.
    """
    with pikepdf.open(input_path) as pdf:
        _recompress_images(pdf, quality=quality, max_dpi=max_dpi)
        pdf.save(output_path, linearize=True)
