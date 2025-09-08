
from __future__ import annotations
from pathlib import Path

def sign_pdf(input_path: str, output_path: str, pfx_path: str, pfx_password: str, reason: str = "Signed by PDFCraft"):
    """
    Simple wiring to pyHanko CLI for digital signing.
    Requires `pyhanko` installed and a PKCS#12 (.pfx/.p12) file.
    """
    import subprocess, shlex
    cmd = f'pyhanko sign addsig --field Sig1 -P "{pfx_password}" -p "{pfx_path}" "{input_path}" "{output_path}"'
    # Note: you can build an in-Python signer via pyHanko APIs;
    # we keep it minimal here for clarity & portability.
    subprocess.run(shlex.split(cmd), check=True)
