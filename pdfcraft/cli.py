from __future__ import annotations
import typer
from typing import List
from pathlib import Path

# NOTE: alias the module to avoid clashing with the CLI function name
from . import core, compress as pdf_compress, ocr, annotate, redact, signing

app = typer.Typer(pretty_exceptions_show_locals=False,
                  help="PDFCraft CLI – Acrobat-like utilities.")

@app.command()
def info(path: str):
    "Show basic PDF info & metadata."
    data = core.info(path)
    import json
    typer.echo(json.dumps(data, indent=2))

@app.command()
def merge(inputs: List[str], output: str):
    "Merge PDFs: pdfcraft merge --output out.pdf in1.pdf in2.pdf ..."
    core.merge_pdfs(inputs, output)
    typer.secho(f"Saved: {output}", fg=typer.colors.GREEN)

@app.command()
def split(input: str, ranges: str, output_dir: str = "splits"):
    "Split by page ranges, e.g., '1-3,7,10-': exports one PDF per page."
    files = core.split_pdf(input, ranges, output_dir)
    typer.secho(f"Wrote {len(files)} files to: {output_dir}", fg=typer.colors.GREEN)

@app.command()
def rotate(input: str, pages: str = "1-", angle: int = 90, output: str = "rotated.pdf"):
    "Rotate selected pages by angle (multiples of 90)."
    core.rotate_pages(input, output, pages, angle)
    typer.secho(f"Saved: {output}", fg=typer.colors.GREEN)

@app.command("extract-text")
def extract_text_cmd(input: str, output_txt: str = "text.txt"):
    "Extract all text to a UTF-8 .txt file."
    core.extract_text(input, output_txt)
    typer.secho(f"Saved: {output_txt}", fg=typer.colors.GREEN)

@app.command("extract-images")
def extract_images_cmd(input: str, output_dir: str = "images"):
    "Extract embedded images to a folder."
    n = core.extract_images(input, output_dir)
    typer.secho(f"Extracted {n} images to: {output_dir}", fg=typer.colors.GREEN)

@app.command("compress")
def compress_cmd(input: str, output: str = "compressed.pdf", quality: int = 60, max_dpi: int = 200):
    "Compress by downsampling & recompressing images (quality 1-95; max_dpi typical 150-300)."
    pdf_compress.compress_pdf(input, output, quality=quality, max_dpi=max_dpi)
    typer.secho(f"Saved: {output}", fg=typer.colors.GREEN)

@app.command()
def ocrpdf(input: str, output: str = "ocr.pdf", dpi: int = 300, lang: str = "eng"):
    "OCR scanned PDFs to make them searchable (needs Tesseract installed)."
    ocr.ocr_pdf(input, output, dpi=dpi, lang=lang)
    typer.secho(f"Saved: {output}", fg=typer.colors.GREEN)

@app.command()
def highlight(input: str, output: str = "highlighted.pdf", text: str = typer.Argument(...)):
    "Highlight all occurrences of TEXT."
    n = annotate.highlight_text(input, output, text)
    typer.secho(f"Highlighted {n} instances. Saved: {output}", fg=typer.colors.GREEN)

@app.command()
def watermark(input: str, output: str = "watermarked.pdf", text: str = typer.Argument(...), opacity: float = 0.15):
    "Apply a diagonal text watermark."
    annotate.watermark_text(input, output, text, opacity)
    typer.secho(f"Saved: {output}", fg=typer.colors.GREEN)

@app.command()
def redact(input: str, output: str = "redacted.pdf", text: str = typer.Argument(...)):
    "Redact all occurrences of TEXT (vector redaction)."
    n = redact.redact_text(input, output, text)
    typer.secho(f"Redacted {n} instances. Saved: {output}", fg=typer.colors.GREEN)

@app.command()
def sign(input: str, output: str = "signed.pdf", pfx: str = typer.Argument(...), pfx_password: str = typer.Option(..., prompt=True, hide_input=True)):
    "Digitally sign using a .pfx/.p12 (requires pyHanko CLI)."
    signing.sign_pdf(input, output, pfx, pfx_password)

if __name__ == "__main__":
    app()
