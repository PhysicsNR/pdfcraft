# PDFCraft

**PDFCraft** is a Python-based PDF toolkit and viewer — like a lightweight, open-source alternative to Acrobat.  
It is continuously upgraded with new features, and contributions are welcome!

Built with [PySide6](https://wiki.qt.io/Qt_for_Python), [PyMuPDF](https://pymupdf.readthedocs.io/), and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).

---

## ✨ Features (Current)
- 📖 Open and view PDFs with thumbnails
- 🔎 Search text in PDFs
- 📝 Highlight, draw, add notes
- 🗂 Insert, delete, reorder pages
- 📉 Compress PDFs
- 🔤 OCR scanned PDFs (make image-based PDFs searchable)
- 🖊 Add headers/footers

---

## 🚀 Getting Started

### Windows
1. Install [Python 3.10+](https://www.python.org/downloads/windows/).
2. Install [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)  
   (make sure it’s added to your PATH).
3. Clone this repo:
   ```bash
   git clone https://github.com/PhysicsNR/pdfcraft.git
   cd pdfcraft
   ```
4. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the GUI:
   ```bash
   python -m gui.app
   ```

### macOS / Linux
```bash
brew install tesseract            # macOS
sudo apt install tesseract-ocr    # Linux

git clone https://github.com/PhysicsNR/pdfcraft.git
cd pdfcraft
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m gui.app
```

---

## 🛠 Roadmap
- [ ] Continuous scrolling + zoom
- [ ] Form filling and editing
- [ ] Digital signatures
- [ ] Cloud sync and collaboration

---

## 📷 Screenshots
![PDFCraft Screenshot](docs/screenshot.png)

---

## 📄 License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
