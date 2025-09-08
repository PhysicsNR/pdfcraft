
from __future__ import annotations
import sys, fitz
from PySide6 import QtWidgets, QtGui, QtCore
from pathlib import Path

# Optional imports for OCR
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

def build_display_transform(label: QtWidgets.QLabel, pix: QtGui.QPixmap):
    lw, lh = label.width(), label.height()
    pw, ph = pix.width(), pix.height()
    if pw == 0 or ph == 0:
        return 1.0, 0.0, 0.0
    scale = min(lw / pw, lh / ph)
    disp_w, disp_h = pw * scale, ph * scale
    offx = (lw - disp_w) / 2.0
    offy = (lh - disp_h) / 2.0
    return scale, offx, offy

def view_to_pix_coords(label: QtWidgets.QLabel, pix: QtGui.QPixmap, pos: QtCore.QPointF):
    scale, offx, offy = build_display_transform(label, pix)
    x = (pos.x() - offx) / scale
    y = (pos.y() - offy) / scale
    return QtCore.QPointF(x, y)

def pix_to_page_xy(pix_pt: QtCore.QPointF, dpi: int):
    return (pix_pt.x() * 72.0 / dpi, pix_pt.y() * 72.0 / dpi)

class ThumbnailList(QtWidgets.QListWidget):
    pageActivated = QtCore.Signal(int)
    pageMoved = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QtCore.QSize(90, 120))
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setMovement(QtWidgets.QListView.Snap)
        self.setFlow(QtWidgets.QListView.LeftToRight)
        self.setWrapping(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setSelectionMode(QtWidgets.QListWidget.SingleSelection)
        self.verticalScrollBar().setSingleStep(12)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        selected = self.currentRow()
        super().dropEvent(event)
        new_idx = self.currentRow()
        if selected != new_idx:
            self.pageMoved.emit(selected, new_idx)

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        super().mousePressEvent(e)
        if e.button() == QtCore.Qt.LeftButton:
            self.pageActivated.emit(self.currentRow())

class PdfCanvas(QtWidgets.QLabel):
    requestStatus = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(700, 900)
        self._pix = None
        self._page = None
        self._dpi = 144
        self.tool = "pan"
        self._dragging = False
        self._drag_start = None
        self._drag_end = None
        self._ink_points = []

    def set_page(self, page: fitz.Page, dpi: int = None):
        if dpi is not None:
            self._dpi = dpi
        self._page = page
        pix = page.get_pixmap(dpi=self._dpi)
        img = QtGui.QImage(pix.samples, pix.width, pix.height, pix.stride, QtGui.QImage.Format_RGB888)
        self._pix = QtGui.QPixmap.fromImage(img)
        self._update_view()

    def _update_view(self):
        if not self._pix:
            return
        self.setPixmap(self._pix.scaled(self.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._pix:
            self._update_view()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if not self._pix or not self._page:
            return
        if e.button() == QtCore.Qt.LeftButton:
            self._dragging = True
            self._drag_start = e.position()
            self._drag_end = e.position()
            if self.tool == "pen":
                self._ink_points = [e.position()]
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if not self._pix or not self._page:
            return
        if self._dragging:
            self._drag_end = e.position()
            if self.tool == "pen":
                self._ink_points.append(e.position())
            self.update()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        if not self._pix or not self._page:
            return
        if e.button() == QtCore.Qt.LeftButton and self._dragging:
            self._dragging = False
            if self.tool == "highlight":
                self._apply_rect_highlight(self._drag_start, self._drag_end)
            elif self.tool == "pen":
                self._apply_ink(self._ink_points)
            elif self.tool == "note":
                self._apply_note(e.position(), "Note")
            self._ink_points = []
            self._drag_start = self._drag_end = None
            self.update()
        super().mouseReleaseEvent(e)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._drag_start and self._drag_end and self.tool in ("highlight", "pen"):
            painter = QtGui.QPainter(self)
            pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.DashLine if self.tool == "highlight" else QtCore.Qt.SolidLine)
            painter.setPen(pen)
            if self.tool == "highlight":
                rect = QtCore.QRectF(self._drag_start, self._drag_end).normalized()
                painter.drawRect(rect)
            elif self.tool == "pen" and len(self._ink_points) > 1:
                for i in range(len(self._ink_points) - 1):
                    painter.drawLine(self._ink_points[i], self._ink_points[i + 1])
            painter.end()

    def _apply_rect_highlight(self, p0: QtCore.QPointF, p1: QtCore.QPointF):
        if not self._pix or not self._page:
            return
        p0_pix = view_to_pix_coords(self, self._pix, p0)
        p1_pix = view_to_pix_coords(self, self._pix, p1)
        x0, y0 = pix_to_page_xy(p0_pix, self._dpi)
        x1, y1 = pix_to_page_xy(p1_pix, self._dpi)
        rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        if rect.width > 0 and rect.height > 0:
            self._page.add_highlight_annot(rect)
            self.requestStatus.emit("Added rectangle highlight")
        self.set_page(self._page, self._dpi)

    def _apply_ink(self, points_view):
        if not self._pix or not self._page or len(points_view) < 2:
            return
        path = []
        for pt in points_view:
            p = view_to_pix_coords(self, self._pix, pt)
            x, y = pix_to_page_xy(p, self._dpi)
            path.append((x, y))
        annot = self._page.add_ink_annot([path])
        annot.set_border(width=1)
        self.requestStatus.emit("Added ink annotation")
        self.set_page(self._page, self._dpi)

    def _apply_note(self, pos_view: QtCore.QPointF, text: str):
        p = view_to_pix_coords(self, self._pix, pos_view)
        x, y = pix_to_page_xy(p, self._dpi)
        self._page.add_text_annot(fitz.Point(x, y), text)
        self.requestStatus.emit("Added text note")
        self.set_page(self._page, self._dpi)

class OcrDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCR Options")
        form = QtWidgets.QFormLayout(self)
        self.spin_dpi = QtWidgets.QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(300)
        self.edit_lang = QtWidgets.QLineEdit("eng")
        self.out_path = QtWidgets.QLineEdit("ocr.pdf")
        btn_browse = QtWidgets.QPushButton("Browse…")
        btn_browse.clicked.connect(self._choose_out)
        h = QtWidgets.QHBoxLayout()
        h.addWidget(self.out_path); h.addWidget(btn_browse)
        form.addRow("DPI:", self.spin_dpi)
        form.addRow("Language(s):", self.edit_lang)
        form.addRow("Save As:", h)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _choose_out(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save OCR Output", self.out_path.text(), "PDF files (*.pdf)")
        if path:
            self.out_path.setText(path)

    def values(self):
        return self.spin_dpi.value(), self.edit_lang.text().strip(), self.out_path.text().strip()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.doc: fitz.Document | None = None
        self.page_index = 0
        self.matches = []
        self.match_i = -1

        self.setWindowTitle("PDFCraft – Pro Viewer")
        self._build_ui()
        self._wire()

    def _build_ui(self):
        self.canvas = PdfCanvas()
        self.sidebar = ThumbnailList()
        self.sidebar.setFixedHeight(160)

        container = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(container)
        v.setContentsMargins(0,0,0,0)
        v.setSpacing(3)
        v.addWidget(self.sidebar)
        v.addWidget(self.canvas, 1)
        self.setCentralWidget(container)

        tb = QtWidgets.QToolBar("Tools")
        tb.setIconSize(QtCore.QSize(22,22))
        self.addToolBar(tb)

        self.act_open = QtGui.QAction("Open", self)
        self.act_save = QtGui.QAction("Save", self)
        self.act_saveas = QtGui.QAction("Save As", self)
        self.act_prev = QtGui.QAction("Prev", self)
        self.act_next = QtGui.QAction("Next", self)
        self.act_delete = QtGui.QAction("Delete Page", self)
        self.act_insert_before = QtGui.QAction("Insert PDF Before...", self)
        self.act_insert_after = QtGui.QAction("Insert PDF After...", self)
        self.act_compress = QtGui.QAction("Compress...", self)
        self.act_ocr = QtGui.QAction("OCR…", self)

        self.find_edit = QtWidgets.QLineEdit()
        self.find_edit.setPlaceholderText("Find text…")
        self.act_find_prev = QtGui.QAction("←", self)
        self.act_find_next = QtGui.QAction("→", self)

        self.tool_group = QtGui.QActionGroup(self)
        self.act_tool_pan = QtGui.QAction("Pan", self, checkable=True)
        self.act_tool_highlight = QtGui.QAction("Highlight", self, checkable=True)
        self.act_tool_pen = QtGui.QAction("Pen", self, checkable=True)
        self.act_tool_note = QtGui.QAction("Note", self, checkable=True)
        for a in (self.act_tool_pan, self.act_tool_highlight, self.act_tool_pen, self.act_tool_note):
            self.tool_group.addAction(a)
        self.act_tool_pan.setChecked(True)

        self.act_stamp_header = QtGui.QAction("Add Header/Footer…", self)

        for a in [self.act_open, self.act_save, self.act_saveas, self.act_prev, self.act_next,
                  self.act_delete, self.act_insert_before, self.act_insert_after, self.act_compress, self.act_ocr]:
            tb.addAction(a)
        tb.addSeparator()
        tb.addWidget(self.find_edit)
        tb.addAction(self.act_find_prev)
        tb.addAction(self.act_find_next)
        tb.addSeparator()
        tb.addAction(self.act_tool_pan)
        tb.addAction(self.act_tool_highlight)
        tb.addAction(self.act_tool_pen)
        tb.addAction(self.act_tool_note)
        tb.addSeparator()
        tb.addAction(self.act_stamp_header)

        self.statusBar().showMessage("Ready")

    def _wire(self):
        self.act_open.triggered.connect(self._open)
        self.act_save.triggered.connect(self._save)
        self.act_saveas.triggered.connect(self._saveas)
        self.act_prev.triggered.connect(self._prev)
        self.act_next.triggered.connect(self._next)
        self.act_delete.triggered.connect(self._delete_page)
        self.act_insert_before.triggered.connect(lambda: self._insert_pdf(where="before"))
        self.act_insert_after.triggered.connect(lambda: self._insert_pdf(where="after"))
        self.act_compress.triggered.connect(self._compress_dialog)
        self.act_ocr.triggered.connect(self._ocr_dialog)
        self.act_find_prev.triggered.connect(lambda: self._find(step=-1))
        self.act_find_next.triggered.connect(lambda: self._find(step=+1))
        self.find_edit.returnPressed.connect(lambda: self._find(step=+1, reset=True))
        self.sidebar.pageActivated.connect(self._go_to_page)
        self.sidebar.pageMoved.connect(self._reorder_pages)
        self.canvas.requestStatus.connect(self.statusBar().showMessage)

        self.act_tool_pan.triggered.connect(lambda: self._set_tool("pan"))
        self.act_tool_highlight.triggered.connect(lambda: self._set_tool("highlight"))
        self.act_tool_pen.triggered.connect(lambda: self._set_tool("pen"))
        self.act_tool_note.triggered.connect(lambda: self._set_tool("note"))
        self.act_stamp_header.triggered.connect(self._stamp_header_footer)

    def _refresh(self):
        if not self.doc: return
        self.page_index = max(0, min(self.page_index, self.doc.page_count-1))
        page = self.doc.load_page(self.page_index)
        self.canvas.set_page(page)
        self._populate_thumbs(select_index=self.page_index)

    def _open(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF files (*.pdf)")
        if not path: return
        self.doc = fitz.open(path)
        self.page_index = 0
        self.setWindowTitle(f"PDFCraft – {Path(path).name}")
        self._populate_thumbs()
        self._refresh()

    def _save(self):
        if not self.doc: return
        target = self.doc.name or ""
        if not target:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", "", "PDF files (*.pdf)")
            if not path: return
            target = path
        self.doc.save(target, deflate=True)
        self.statusBar().showMessage(f"Saved: {target}", 4000)

    def _saveas(self):
        if not self.doc: return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save As", "", "PDF files (*.pdf)")
        if not path: return
        self.doc.save(path, deflate=True, incremental=False)
        self.statusBar().showMessage(f"Saved: {path}", 4000)

    def _prev(self):
        if not self.doc: return
        self.page_index = max(0, self.page_index - 1)
        self._refresh()

    def _next(self):
        if not self.doc: return
        self.page_index = min(self.doc.page_count - 1, self.page_index + 1)
        self._refresh()

    def _go_to_page(self, idx: int):
        if not self.doc: return
        self.page_index = max(0, min(idx, self.doc.page_count-1))
        self._refresh()

    def _delete_page(self):
        if not self.doc: return
        if self.doc.page_count <= 1:
            QtWidgets.QMessageBox.warning(self, "PDFCraft", "Cannot delete the last page.")
            return
        self.doc.delete_page(self.page_index)
        self.page_index = max(0, self.page_index - 1)
        self._refresh()

    def _reorder_pages(self, src: int, dst: int):
        if not self.doc: return
        if src == dst: return
        self.doc.move_page(src, dst)
        self.page_index = dst
        self._refresh()

    def _insert_pdf(self, where: str):
        if not self.doc: return
        other, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Insert PDF", "", "PDF files (*.pdf)")
        if not other: return
        with fitz.open(other) as src:
            pos = self.page_index + (1 if where == "after" else 0)
            self.doc.insert_pdf(src, start=0, end=src.page_count-1, start_at=pos)
        self._refresh()

    def _compress_dialog(self):
        if not self.doc: return
        out_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Compressed As", "", "PDF files (*.pdf)")
        if not out_path: return
        try:
            try:
                self.doc.save(out_path, deflate=True, linear=True)
            except Exception:
                self.doc.save(out_path, deflate=True)
            QtWidgets.QMessageBox.information(self, "PDFCraft", f"Saved: {out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "PDFCraft", f"Compression failed:\n{e}")

    def _ocr_dialog(self):
        if not self.doc:
            QtWidgets.QMessageBox.information(self, "PDFCraft", "Open a PDF first.")
            return
        if not OCR_AVAILABLE:
            QtWidgets.QMessageBox.critical(self, "PDFCraft", "OCR dependencies not found.\nInstall: Pillow, pytesseract, and system Tesseract.")
            return

        dlg = OcrDialog(self)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        dpi, lang, out_path = dlg.values()
        if not out_path:
            QtWidgets.QMessageBox.warning(self, "PDFCraft", "Please choose an output path.")
            return

        if sys.platform.startswith("win"):
            import os
            default_exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            cmd = os.getenv("TESSERACT_EXE", default_exe)
            if os.path.exists(cmd):
                import pytesseract as _pt
                _pt.pytesseract.tesseract_cmd = cmd

        try:
            out = fitz.open()
            progress = QtWidgets.QProgressDialog("OCR running…", "Cancel", 0, self.doc.page_count, self)
            progress.setWindowModality(QtCore.Qt.ApplicationModal)
            progress.setMinimumDuration(0)
            for i in range(self.doc.page_count):
                if progress.wasCanceled():
                    break
                page = self.doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
                p = fitz.open(stream=pdf_bytes, filetype="pdf")
                out.insert_pdf(p)
                p.close()
                progress.setValue(i+1)
                QtWidgets.QApplication.processEvents()
            if not progress.wasCanceled():
                try:
                    out.save(out_path, deflate=True, linear=True)
                except Exception:
                    out.save(out_path, deflate=True)
                QtWidgets.QMessageBox.information(self, "PDFCraft", f"OCR saved: {out_path}")
            out.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "PDFCraft", f"OCR failed:\n{e}")

    def _set_tool(self, name: str):
        self.canvas.tool = name
        self.statusBar().showMessage(f"Tool: {name}")

    def _find(self, step: int = +1, reset: bool = False):
        if not self.doc: return
        q = self.find_edit.text().strip()
        if not q:
            return

        FLAG_IGNORECASE  = getattr(fitz, "TEXT_IGNORECASE", 0) or getattr(fitz, "TEXT_SEARCH_IGNORECASE", 0)
        FLAG_DEHYPHENATE = getattr(fitz, "TEXT_DEHYPHENATE", 0)
        flags = (FLAG_IGNORECASE | FLAG_DEHYPHENATE)

        if reset or not getattr(self, "matches", []):
            self.matches = []
            for pi in range(self.doc.page_count):
                page = self.doc.load_page(pi)
                try:
                    rects = page.search_for(q, flags=flags) if flags else page.search_for(q)
                except TypeError:
                    rects = page.search_for(q)
                for r in rects:
                    self.matches.append((pi, r))
            if not self.matches:
                self.statusBar().showMessage("No matches")
                return
            self.match_i = -1

        self.match_i = (self.match_i + step) % len(self.matches)
        pi, r = self.matches[self.match_i]
        self.page_index = pi
        self._refresh()
        page = self.doc.load_page(pi)
        annot = page.add_rect_annot(r)
        annot.set_colors(stroke=(1, 0, 0))
        annot.set_border(width=1)
        annot.update()
        self.canvas.set_page(page)
        self.statusBar().showMessage(f"Match {self.match_i+1}/{len(self.matches)} on page {pi+1}")

    def _populate_thumbs(self, select_index: int | None = None):
        if not self.doc: return
        self.sidebar.clear()
        for i in range(self.doc.page_count):
            page = self.doc.load_page(i)
            pix = page.get_pixmap(dpi=72)
            qimg = QtGui.QImage(pix.samples, pix.width, pix.height, pix.stride, QtGui.QImage.Format_RGB888)
            icon = QtGui.QIcon(QtGui.QPixmap.fromImage(qimg).scaled(90, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            item = QtWidgets.QListWidgetItem(icon, str(i+1))
            self.sidebar.addItem(item)
        if select_index is not None and 0 <= select_index < self.sidebar.count():
            self.sidebar.setCurrentRow(select_index)

    def _stamp_header_footer(self):
        if not self.doc: return
        dlg = StampDialog(self)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        top_text, bottom_text, size = dlg.get_values()
        for i in range(self.doc.page_count):
            page = self.doc.load_page(i)
            r = page.rect
            if top_text:
                page.insert_textbox(fitz.Rect(r.x0+36, r.y0+12, r.x1-36, r.y0+48), top_text,
                                    fontsize=size, color=(0,0,0), align=fitz.TEXT_ALIGN_CENTER)
            if bottom_text:
                page.insert_textbox(fitz.Rect(r.x0+36, r.y1-48, r.x1-36, r.y1-12), bottom_text,
                                    fontsize=size, color=(0,0,0), align=fitz.TEXT_ALIGN_CENTER)
        self._refresh()
        self.statusBar().showMessage("Stamped header/footer")

class StampDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Header / Footer")
        lay = QtWidgets.QFormLayout(self)
        self.top = QtWidgets.QLineEdit()
        self.bot = QtWidgets.QLineEdit()
        self.size = QtWidgets.QSpinBox(); self.size.setRange(6, 48); self.size.setValue(10)
        lay.addRow("Header text:", self.top)
        lay.addRow("Footer text:", self.bot)
        lay.addRow("Font size:", self.size)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok|QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def get_values(self):
        return self.top.text().strip(), self.bot.text().strip(), self.size.value()

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.resize(1100, 1100)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
