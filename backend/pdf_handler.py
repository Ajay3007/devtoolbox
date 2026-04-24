"""
PDF Handler — text extraction and editing using PyMuPDF (fitz).
"""
import os
import base64
from datetime import datetime

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False


class PDFHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #
    def _check_fitz(self):
        try:
            import fitz
            global fitz
        except ImportError:
            raise RuntimeError(
                "PyMuPDF is not installed. Run: pip install PyMuPDF"
            )


    def _resolve(self, filepath):
        """Return an absolute path that exists, or raise FileNotFoundError."""
        for candidate in [
            filepath,
            os.path.join(self.upload_folder, filepath),
            os.path.join(self.upload_folder, os.path.basename(filepath)),
        ]:
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
        raise FileNotFoundError(f"PDF not found: {filepath}")

    @staticmethod
    def _color_int_to_rgb(color_int):
        r = ((color_int >> 16) & 0xFF) / 255
        g = ((color_int >> 8) & 0xFF) / 255
        b = (color_int & 0xFF) / 255
        return [round(r, 4), round(g, 4), round(b, 4)]

    @staticmethod
    def _flags_to_font(font_name, flags):
        """Map flags + original font name to a PyMuPDF built-in font."""
        is_bold   = bool(flags & 16)
        is_italic = bool(flags & 2)
        fn = font_name.lower()
        if "courier" in fn or "mono" in fn:
            base = "cour"
        elif "times" in fn or "serif" in fn:
            base = "tiro" if not is_bold else "tibo"
            if is_italic:
                base = "tiit" if not is_bold else "tibi"
        else:                               # Helvetica / sans-serif default
            base = "helv"
            if is_bold and is_italic:
                base = "helv-bi"
            elif is_bold:
                base = "helv-b"
            elif is_italic:
                base = "helv-o"
        return base

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #
    def get_info(self, filepath):
        self._check_fitz()
        path = self._resolve(filepath)
        doc = fitz.open(path)
        try:
            return {
                "success": True,
                "filename": os.path.basename(path),
                "filepath": filepath,
                "page_count": len(doc),
                "metadata": {
                    "title":   doc.metadata.get("title", ""),
                    "author":  doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                    "creator": doc.metadata.get("creator", ""),
                },
            }
        finally:
            doc.close()

    def render_page(self, filepath, page_num, scale=1.5):
        self._check_fitz()
        path = self._resolve(filepath)
        doc = fitz.open(path)
        try:
            if page_num < 0 or page_num >= len(doc):
                return {"success": False, "error": "Invalid page number"}
            page = doc[page_num]
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_b64 = base64.b64encode(pix.tobytes("png")).decode()
            return {
                "success":      True,
                "image":        img_b64,
                "img_width":    pix.width,
                "img_height":   pix.height,
                "page_width":   page.rect.width,
                "page_height":  page.rect.height,
                "scale":        scale,
            }
        finally:
            doc.close()

    def get_text_blocks(self, filepath, page_num):
        self._check_fitz()
        path = self._resolve(filepath)
        doc = fitz.open(path)
        try:
            if page_num < 0 or page_num >= len(doc):
                return {"success": False, "error": "Invalid page number"}
            page = doc[page_num]
            raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            spans = []
            sid = 0
            for block in raw.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if not text.strip():
                            continue
                        color_int = span.get("color", 0)
                        spans.append({
                            "id":        sid,
                            "text":      text,
                            "bbox":      list(span.get("bbox", [0, 0, 0, 0])),
                            "font":      span.get("font", "Helvetica"),
                            "size":      round(span.get("size", 12), 2),
                            "flags":     span.get("flags", 0),
                            "color_int": color_int,
                            "color_rgb": self._color_int_to_rgb(color_int),
                        })
                        sid += 1
            return {"success": True, "page_num": page_num, "spans": spans}
        finally:
            doc.close()

    def apply_edits(self, filepath, edits, output_name=None, deleted_pages=None, metadata=None, watermark=None):
        """
        deleted_pages: list of 0-indexed page numbers to delete.
        metadata: optional dict containing title, author, subject, creator to apply.
        watermark: optional dict { text: str, color_rgb: [r,g,b], opacity: float }
        edits: list of {
            page: int,
            action: 'replace' | 'redact',
            bbox: [x0, y0, x1, y1],
            new_text: str, (optional for redact)
            font: str,
            size: float,
            flags: int,
            color_rgb: [r, g, b]   (0-1 range)
        }
        """
        self._check_fitz()
        path = self._resolve(filepath)
        doc = fitz.open(path)
        try:
            # 1. Delete pages if requested
            if deleted_pages:
                # Sort descending to avoid index shifting issues during deletion
                for p in sorted(set(deleted_pages), reverse=True):
                    if 0 <= p < len(doc):
                        doc.delete_page(p)
                
                # Shift edit page indexes to account for deletions
                shifted_edits = []
                for e in edits:
                    old_p = e.get("page", 0)
                    if old_p in deleted_pages:
                        continue # Edit is on a deleted page, discard it
                    
                    # Calculate new page index
                    shift = sum(1 for dp in deleted_pages if dp < old_p)
                    e["page"] = old_p - shift
                    shifted_edits.append(e)
                edits = shifted_edits

            # 2. Group by page
            by_page = {}
            for e in edits:
                pg = e.get("page", 0)
                by_page.setdefault(pg, []).append(e)

            for page_num, page_edits in by_page.items():
                if page_num < 0 or page_num >= len(doc):
                    continue
                page = doc[page_num]

                # Pass 1 — redact (erase) all original bboxes
                for e in page_edits:
                    rect = fitz.Rect(e["bbox"])
                    action = e.get("action", "replace")
                    if action == "redact":
                        page.add_redact_annot(rect, fill=(0, 0, 0)) # Fill black for redact
                    else:
                        page.add_redact_annot(rect, fill=(1, 1, 1)) # Fill white for replace
                page.apply_redactions()

                # Pass 2 — insert new text into each bbox (only for 'replace' action)
                for e in page_edits:
                    action = e.get("action", "replace")
                    if action == "redact":
                        continue
                        
                    rect  = fitz.Rect(e["bbox"])
                    fsize = float(e.get("size", 12))
                    color = tuple(e.get("color_rgb", [0, 0, 0]))
                    flags = int(e.get("flags", 0))
                    fname = e.get("font", "Helvetica")
                    builtin = self._flags_to_font(fname, flags)

                    tw = fitz.TextWriter(page.rect)
                    try:
                        font = fitz.Font(builtin)
                        # Baseline: bottom of bbox minus small descender gap
                        tw.append(
                            (rect.x0, rect.y1 - fsize * 0.18),
                            e.get("new_text", ""),
                            font=font,
                            fontsize=fsize,
                        )
                        tw.write_text(page, color=color)
                    except Exception:
                        # Absolute fallback
                        page.insert_text(
                            (rect.x0, rect.y1 - 2),
                            e.get("new_text", ""),
                            fontsize=fsize,
                            color=color,
                        )

            # 3. Apply metadata if requested
            if metadata:
                doc.set_metadata({
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "creator": metadata.get("creator", ""),
                })

            # 4. Apply global watermark if requested
            if watermark and watermark.get("text"):
                w_text = watermark["text"]
                w_color = tuple(watermark.get("color_rgb", [0.75, 0.75, 0.75]))
                
                # We blend the color towards white based on opacity to simulate transparency
                # Formula: blended = color * opacity + 1.0 * (1 - opacity)
                opacity = float(watermark.get("opacity", 0.3))
                blended_color = tuple(c * opacity + 1.0 * (1 - opacity) for c in w_color)

                import math
                for page in doc:
                    rect = page.rect
                    # Calculate angle from bottom-left to top-right
                    angle = math.degrees(math.atan2(rect.height, rect.width))
                    
                    # Calculate font size to fit diagonally
                    diag_len = math.hypot(rect.width, rect.height)
                    fsize = diag_len / max(len(w_text), 1) * 1.4
                    
                    # Center point
                    center = fitz.Point(rect.width / 2, rect.height / 2)
                    
                    # Estimate width to shift start point so it looks centered
                    # len * fsize * 0.5 is a rough estimate for text width
                    text_width = len(w_text) * fsize * 0.45
                    
                    # We start drawing from the center shifted back by half the text width horizontally.
                    start_pt = fitz.Point(center.x - text_width/2, center.y + fsize/3)
                    
                    # Since Y goes down, a negative angle rotates "up" from left to right
                    mat = fitz.Matrix(-angle)
                    
                    # Insert text with morph
                    page.insert_text(
                        start_pt,
                        w_text,
                        fontsize=fsize,
                        color=blended_color,
                        fontname="helv",
                        morph=(center, mat)
                    )

            # Build output filename
            if output_name:
                safe = os.path.basename(output_name)
                if not safe.lower().endswith(".pdf"):
                    safe += ".pdf"
            else:
                base = os.path.splitext(os.path.basename(path))[0]
                ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe = f"{base}_edited_{ts}.pdf"

            out_path = os.path.join(self.upload_folder, safe)
            doc.save(out_path, garbage=4, deflate=True)
            return {
                "success":       True,
                "filename":      safe,
                "output_path":   out_path,
                "edits_applied": len(edits),
            }
        finally:
            doc.close()

    def append_pdf(self, main_filepath, append_filepath):
        """Append one PDF to the end of another and save in place."""
        self._check_fitz()
        main_path = self._resolve(main_filepath)
        append_path = self._resolve(append_filepath)
        
        doc1 = fitz.open(main_path)
        doc2 = fitz.open(append_path)
        try:
            doc1.insert_pdf(doc2)
            temp_path = main_path + ".tmp"
            doc1.save(temp_path, garbage=4, deflate=True)
            new_len = len(doc1)
            doc1.close()
            doc2.close()
            
            # Replace original with the new appended file
            import shutil
            shutil.move(temp_path, main_path)
            
            return {
                "success": True,
                "page_count": new_len,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if not doc1.is_closed:
                doc1.close()
            if not doc2.is_closed:
                doc2.close()

