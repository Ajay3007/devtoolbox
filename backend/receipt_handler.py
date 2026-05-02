"""
Receipt Handler — Smart image-based receipt editing.

Workflow:
  1. Upload JPG/PNG/PDF scan → OCR → return structured fields + all word spans
  2. User edits field values in the UI
  3. For each edit: pixel-level ink removal (preserving background/stamps) + re-render text
  4. Output: high-res PNG → PDF

Preserves paper grain and stamp impressions by masking only dark ink pixels.
"""

import os
import io
import re
import base64
from datetime import datetime

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import pytesseract

# ---------------------------------------------------------------------------
# Known field patterns for HP fuel receipts (regex → display label)
# ---------------------------------------------------------------------------
KNOWN_FIELDS = [
    (r"bill\s*no?\.?",       "Bill No"),
    (r"trns\.?\s*id",        "Transaction ID"),
    (r"atnd\.?\s*id",        "Attendant ID"),
    (r"receipt",             "Receipt"),
    (r"vehi\.?\s*no?\.?",    "Vehicle No"),
    (r"mob\.?\s*no?\.?",     "Mobile No"),
    (r"date",                "Date"),
    (r"time",                "Time"),
    (r"fp\.?\s*id",          "FP ID"),
    (r"nozl?\s*no?\.?",      "Nozzle No"),
    (r"^fuel$",              "Fuel"),
    (r"density",             "Density"),
    (r"preset",              "Preset"),
    (r"rate",                "Rate"),
    (r"sale",                "Sale"),
    (r"volume",              "Volume"),
]

# Monospace bold fonts in priority order (Mac, Linux, Windows)
FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
    "/Library/Fonts/Courier New Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    r"C:\Windows\Fonts\courbd.ttf",
]


def _find_font():
    for p in FONT_PATHS:
        if os.path.isfile(p):
            return p
    return None


_FONT_PATH = _find_font()


class ReceiptHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder

    # ------------------------------------------------------------------ #
    #  Font helpers
    # ------------------------------------------------------------------ #

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if _FONT_PATH:
            try:
                return ImageFont.truetype(_FONT_PATH, size)
            except Exception:
                pass
        return ImageFont.load_default()

    def _match_font_size(self, sample: str, target_h_px: int) -> int:
        """Binary-search for the PIL font size whose cap-height ≈ target_h_px."""
        if not _FONT_PATH:
            return max(8, int(target_h_px * 0.75))
        lo, hi = 4, 400
        while lo < hi:
            mid = (lo + hi + 1) // 2
            font = ImageFont.truetype(_FONT_PATH, mid)
            try:
                bb = font.getbbox(sample or "Xg")
                h = bb[3] - bb[1]
            except Exception:
                h = mid
            if h <= target_h_px:
                lo = mid
            else:
                hi = mid - 1
        return lo

    # ------------------------------------------------------------------ #
    #  OCR helpers
    # ------------------------------------------------------------------ #

    def _preprocess_for_ocr(self, img: Image.Image) -> Image.Image:
        """Grayscale → contrast boost → adaptive binarisation."""
        gray = img.convert("L")
        gray = ImageEnhance.Contrast(gray).enhance(3.0)
        gray = ImageEnhance.Sharpness(gray).enhance(2.0)
        arr = np.array(gray, dtype=np.float32)
        mean_val = arr.mean()
        thresh = float(min(mean_val * 0.88, 200))
        binary = gray.point(lambda p: 255 if p > thresh else 0)
        return binary

    def _run_ocr(self, img: Image.Image, lang: str = "eng") -> dict:
        processed = self._preprocess_for_ocr(img)
        return pytesseract.image_to_data(
            processed, lang=lang,
            output_type=pytesseract.Output.DICT,
            config="--psm 6 --oem 3",
        )

    # ------------------------------------------------------------------ #
    #  Field parsing
    # ------------------------------------------------------------------ #

    def _parse_fields(self, ocr: dict, img_w: int, img_h: int) -> list:
        """
        Group OCR words into lines, detect label : value pairs,
        and map labels to known field types.

        Handles all colon layouts:
          Case A  "Date"  ":29/04/2026"   → colon at start of value word
          Case B  "Rate"  ":Rs.103.76"    → same
          Case C  "Bill"  "No:Apr-882977" → colon embedded mid-word
          Case D  "Date"  ":"  "29/04/2026" → colon as separate word
        """
        words = []
        n = len(ocr["text"])
        for i in range(n):
            txt = (ocr["text"][i] or "").strip()
            if not txt or int(ocr["conf"][i]) < 5:
                continue
            words.append({
                "text":   txt,
                "left":   ocr["left"][i],
                "top":    ocr["top"][i],
                "width":  ocr["width"][i],
                "height": ocr["height"][i],
            })

        # Group into visual lines by Y-band (robust across Tesseract block splits).
        # Use vertical centre of each word so tall vs short glyphs land on same band.
        BAND = 10  # px — words within this many px (centre-to-centre) share a line
        line_map: dict = {}
        for w in words:
            y_key = round((w["top"] + w["height"] / 2) / BAND)
            line_map.setdefault(y_key, []).append(w)

        # Sort lines top-to-bottom
        sorted_lines = sorted(line_map.values(),
                              key=lambda ws: min(w["top"] for w in ws))

        fields = []
        for line in sorted_lines:
            line = sorted(line, key=lambda w: w["left"])

            # Find first word that contains ':'
            colon_idx = None
            for i, w in enumerate(line):
                if ":" in w["text"]:
                    colon_idx = i
                    break
            if colon_idx is None:
                continue

            cw       = line[colon_idx]
            cw_text  = cw["text"]
            colon_pos_in_word = cw_text.index(":")
            before_colon = cw_text[:colon_pos_in_word]   # e.g. "No" or ""
            after_colon  = cw_text[colon_pos_in_word + 1:]  # e.g. "Apr-882977" or "29/04/2026"

            # Build label text
            label_parts = [w["text"] for w in line[:colon_idx]]
            if before_colon:
                label_parts.append(before_colon)
            label_text = " ".join(label_parts).strip()
            if not label_text:
                continue

            # Build value text — always prefixed with ':' so the span is colon-inclusive
            value_words = line[colon_idx + 1:]  # separate words after colon word
            value_parts = []
            if after_colon:
                value_parts.append(after_colon)
            value_parts += [w["text"] for w in value_words]
            value_text = ":" + " ".join(value_parts).strip()

            # ── Value bbox: starts at the ':' column, with gap-aware x0 ────
            if value_words:
                # Case D: standalone colon word — gap before colon.
                # Shift x0 one colon-word-width to the left so rendered value
                # aligns with the original colon column.
                colon_char_w = cw["width"]   # width of the ':' token
                x0 = max(0, cw["left"] - colon_char_w)
                y0 = cw["top"]
                x1 = max(w["left"] + w["width"]  for w in value_words)
                y1 = max(w["top"]  + w["height"] for w in value_words)
                value_bbox = [x0, y0, x1, y1]

            elif after_colon:
                # Cases A/B/C: colon is embedded in the word.
                char_w = cw["width"] / max(len(cw_text), 1)
                if colon_pos_in_word == 0:
                    # Colon at word start — gap case: extend one char_w left.
                    x0 = max(0, int(cw["left"] - char_w))
                else:
                    # Label immediately before colon — start exactly at ':'.
                    x0 = int(cw["left"] + char_w * colon_pos_in_word)
                y0 = cw["top"]
                x1 = cw["left"] + cw["width"]
                y1 = cw["top"] + cw["height"]
                value_bbox = [x0, y0, x1, y1]

            else:
                # Lone colon at end of word with no value found
                value_bbox = None

            # Use 33rd-percentile height (not median) so that a 2-word line
            # (e.g. "Time" + ":16:51:06") doesn't return the larger inflated value.
            heights = sorted(w["height"] for w in line)
            line_height = heights[max(0, len(heights) // 3)] if heights else 20

            # Match label to a known field type
            field_type = None
            for pattern, name in KNOWN_FIELDS:
                if re.search(pattern, label_text.lower()):
                    field_type = name
                    break

            fields.append({
                "label":       label_text,
                "field_type":  field_type,
                "value":       value_text,
                "value_bbox":  value_bbox,
                "line_height": line_height,
            })

        # Normalize value_bbox x0 to the median colon-column so all values
        # align regardless of which OCR path computed them (Case A vs D).
        x0_list = [f["value_bbox"][0] for f in fields if f["value_bbox"]]
        if len(x0_list) >= 3:
            x0_list_s = sorted(x0_list)
            median_x0 = x0_list_s[len(x0_list_s) // 2]
            for f in fields:
                if f["value_bbox"] and abs(f["value_bbox"][0] - median_x0) < 40:
                    f["value_bbox"][0] = median_x0

        return fields

    def _all_spans(self, ocr: dict) -> list:
        spans = []
        n = len(ocr["text"])
        for i in range(n):
            txt = (ocr["text"][i] or "").strip()
            # Accept conf >= 0 (exclude -1 = invalid).  Low-conf words (e.g.
            # Rate/Density obscured by stamp) would be lost at threshold 5.
            if not txt or int(ocr["conf"][i]) < 0:
                continue
            x = ocr["left"][i]
            y = ocr["top"][i]
            w = ocr["width"][i]
            h = ocr["height"][i]

            # Skip lone colons — structural punctuation, never editable.
            if txt == ':':
                continue

            colon_pos = txt.find(':')
            if colon_pos >= 0:
                after  = txt[colon_pos + 1:]
                before = txt[:colon_pos]

                if not after.strip():
                    # Colon at end (label only, e.g. "Atnd.ID:") — skip entirely.
                    continue

                # Strip label prefix up to and including the colon when the text
                # before the colon has no digits (structural colon, not e.g. time).
                # "No:Apr-882977" → "Apr-882977"  (skip 3 chars)
                # ":29/04/2026"   → "29/04/2026"  (skip 1 char)
                # "16:51:06"      → unchanged (digit before colon)
                if not any(c.isdigit() for c in before):
                    char_w = w / max(len(txt), 1)
                    if colon_pos == 0:
                        # Colon is at the start of the word — there was a gap
                        # between the label and the colon (separate OCR tokens).
                        # Rate/Sale/Volume land here; extending one char_w left
                        # prevents the rendered value from shifting right.
                        extra = int(char_w)
                        x     = max(0, x - extra)
                        w     = w + extra
                        # txt stays ':value' — no label to strip
                    else:
                        # Label text immediately precedes the colon in the same
                        # OCR word (e.g. "No:Apr-882977") — skip only the label.
                        label_skip = int(char_w * colon_pos)
                        txt        = txt[colon_pos:]
                        x         += label_skip
                        w          = max(w - label_skip, 1)

            else:
                # No colon in this word.  Skip pure-label words (all alphabetic +
                # punctuation, no digits) that are short — these are field names
                # like "Date", "Time", "Preset" appearing as standalone words.
                # Keep words with digits or longer mixed words (values like
                # "NotEntered", "Physical", "PRESET" that users may want to edit).
                if (len(txt) <= 8
                        and not any(c.isdigit() for c in txt)
                        and all(c.isalpha() or c in '._- ' for c in txt)):
                    # Match against known field label patterns — skip if it's a label
                    if any(re.search(p, txt.lower()) for p, _ in KNOWN_FIELDS):
                        continue

            if not txt:
                continue

            spans.append({
                "text":   txt,
                "bbox":   [x, y, x + w, y + h],
                "height": h,
                "conf":   int(ocr["conf"][i]),
            })
        return spans

    # ------------------------------------------------------------------ #
    #  Image processing — inpaint + re-render
    # ------------------------------------------------------------------ #

    def _sample_background(self, arr: np.ndarray, bbox: list, margin: int = 8) -> tuple:
        """Sample the background colour from the border surrounding the bbox."""
        x0, y0, x1, y1 = [int(v) for v in bbox]
        h, w = arr.shape[:2]
        bx0 = max(0, x0 - margin)
        by0 = max(0, y0 - margin)
        bx1 = min(w, x1 + margin)
        by1 = min(h, y1 + margin)

        strips = []
        if by0 < y0:
            strips.append(arr[by0:y0, bx0:bx1].reshape(-1, 3))
        if y1 < by1:
            strips.append(arr[y1:by1, bx0:bx1].reshape(-1, 3))
        if bx0 < x0:
            strips.append(arr[by0:by1, bx0:x0].reshape(-1, 3))
        if x1 < bx1:
            strips.append(arr[by0:by1, x1:bx1].reshape(-1, 3))

        if not strips:
            return (255, 255, 255)

        all_px = np.vstack(strips).astype(np.float32)
        # Exclude very dark (ink) pixels from the background estimate
        lum = 0.299 * all_px[:, 0] + 0.587 * all_px[:, 1] + 0.114 * all_px[:, 2]
        bg = all_px[lum > 160]
        if len(bg) == 0:
            bg = all_px
        mean = bg.mean(axis=0).astype(int)
        return (int(mean[0]), int(mean[1]), int(mean[2]))

    def _inpaint_bbox(self, img: Image.Image, bbox: list, bg_color: tuple) -> Image.Image:
        """
        Remove ink within bbox while preserving the background texture
        (paper grain, faint stamps).  Uses OpenCV TELEA inpainting so that
        the stamp impression is reconstructed from surrounding pixels.
        """
        x0, y0, x1, y1 = [int(v) for v in bbox]
        arr = np.array(img.convert("RGB"))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # Build ink mask: combine Otsu + fixed threshold to catch
        # lighter/gray ink pixels that Otsu alone misses (shadow removal)
        region = gray[y0:y1, x0:x1]
        if region.size == 0:
            return img
        _, otsu_mask = cv2.threshold(
            region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        _, fixed_mask = cv2.threshold(region, 180, 255, cv2.THRESH_BINARY_INV)
        region_mask = cv2.bitwise_or(otsu_mask, fixed_mask)

        # Dilate with larger kernel to fully cover anti-aliased/ghost edges
        kernel = np.ones((3, 3), np.uint8)
        region_mask = cv2.dilate(region_mask, kernel, iterations=2)

        # Full-image mask (only the bbox region is non-zero)
        mask = np.zeros(gray.shape, dtype=np.uint8)
        mask[y0:y1, x0:x1] = region_mask

        # TELEA inpainting reconstructs background from surrounding context
        result = cv2.inpaint(arr, mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)
        return Image.fromarray(result)

    def _render_text(self, img: Image.Image, bbox: list,
                     text: str, line_height: int,
                     color: tuple = (0, 0, 0)) -> Image.Image:
        """Draw new text into bbox with auto-matched font size."""
        x0, y0, x1, y1 = [int(v) for v in bbox]
        bbox_h = max(y1 - y0, 1)
        # Cap target height at line_height to prevent oversized text when the
        # OCR bounding box is taller than a normal text line (e.g. stamp overlap).
        target_h = min(bbox_h, line_height) if line_height > 0 else bbox_h
        font_size = self._match_font_size(text, int(target_h * 0.90))
        font = self._get_font(font_size)
        draw = ImageDraw.Draw(img)
        try:
            bb = font.getbbox(text)
            text_h = bb[3] - bb[1]
            # Vertically centre text within the bbox
            y_pos = y0 + (bbox_h - text_h) // 2 - bb[1]
        except Exception:
            y_pos = y0 + 2
        draw.text((x0, y_pos), text, font=font, fill=color)
        return img

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def upload_and_scan(self, file, lang: str = "eng") -> dict:
        """
        Accept a JPG/PNG/PDF upload, OCR it, and return:
          - base64 preview image
          - structured fields list
          - all OCR word spans (for free-form editing)
        """
        ext = os.path.splitext(file.filename)[1].lower()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"receipt_{ts}{ext}"
        save_path = os.path.join(self.upload_folder, safe_name)
        file.save(save_path)

        # Load as PIL Image
        if ext == ".pdf":
            import fitz
            doc = fitz.open(save_path)
            page = doc[0]
            scale = 300 / 72
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            work_name = safe_name.replace(".pdf", ".png")
            work_path = os.path.join(self.upload_folder, work_name)
            img.save(work_path, "PNG", dpi=(300, 300))
        else:
            img = Image.open(save_path).convert("RGB")
            work_name = safe_name
            work_path = save_path

        img_w, img_h = img.size

        # Run OCR on the working image
        ocr = self._run_ocr(img, lang)

        fields    = self._parse_fields(ocr, img_w, img_h)
        all_spans = self._all_spans(ocr)

        # Normalize inflated span heights (and bbox y1).
        # With conf=0, low-conf noise spans (stamps, watermarks) can have very
        # large heights that inflate the median → cap_h too large → Time not capped.
        # Fix: compute reference height only from high-confidence spans (conf≥20).
        if all_spans:
            hc_heights = sorted(s["height"] for s in all_spans if s["conf"] >= 20)
            if len(hc_heights) >= 3:
                # Use the 33rd-percentile of high-conf heights as the reference.
                # Percentile is more robust than median when many normal-height
                # words are present alongside a few inflated OCR boxes.
                ref_h = hc_heights[max(0, len(hc_heights) // 3)]
            elif all_spans:
                hs = sorted(s["height"] for s in all_spans)
                ref_h = hs[len(hs) // 2]
            else:
                ref_h = 30
            cap_h = int(ref_h * 1.3)
            for s in all_spans:
                if s["height"] > cap_h:
                    s["bbox"][3] = s["bbox"][1] + ref_h
                    s["height"]  = ref_h

        # Build preview (cap longest dimension at 1400px)
        preview_img = img.copy()
        max_dim = 1400
        if max(img_w, img_h) > max_dim:
            ratio = max_dim / max(img_w, img_h)
            preview_img = img.resize(
                (int(img_w * ratio), int(img_h * ratio)), Image.LANCZOS
            )
        buf = io.BytesIO()
        preview_img.save(buf, format="JPEG", quality=92)
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        return {
            "success":       True,
            "filepath":      work_name,
            "filename":      file.filename,
            "img_width":     img_w,
            "img_height":    img_h,
            "image_b64":     img_b64,
            "preview_width": preview_img.width,
            "preview_height":preview_img.height,
            "fields":        fields,
            "all_spans":     all_spans,
            "lang":          lang,
            "font_available": _FONT_PATH is not None,
        }

    def process_edits(self, filepath: str, edits: list,
                      output_format: str = "pdf") -> dict:
        """
        Apply edits to the original image.

        edits: [{ bbox:[x0,y0,x1,y1], new_text:str, line_height:float }, ...]
        """
        path = os.path.join(self.upload_folder, os.path.basename(filepath))
        if not os.path.exists(path):
            raise FileNotFoundError(f"Receipt image not found: {filepath}")

        img = Image.open(path).convert("RGB")
        arr = np.array(img)

        for edit in edits:
            bbox      = edit["bbox"]
            new_text  = edit.get("new_text") or ""
            line_h    = int(edit.get("line_height") or 20)

            if new_text == "":
                continue

            # Span now covers colon+value, so we can use a small symmetric padding.
            iw, ih = img.size
            pbbox = [
                max(0, bbox[0] - 3),    # left:   catch colon left-edge anti-aliasing
                max(0, bbox[1] - 4),    # top:    ascenders
                min(iw, bbox[2] + 5),   # right:  last char trailing pixels
                min(ih, bbox[3] + 4),   # bottom: descenders
            ]

            bg_color = self._sample_background(np.array(img), pbbox)
            img = self._inpaint_bbox(img, pbbox, bg_color)
            img = self._render_text(img, bbox, new_text, line_h)

        # Save result
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(os.path.basename(filepath))[0]

        if output_format == "pdf":
            out_name = f"{base}_edited_{ts}.pdf"
            out_path = os.path.join(self.upload_folder, out_name)
            img.save(out_path, "PDF", resolution=300)
        else:
            out_name = f"{base}_edited_{ts}.png"
            out_path = os.path.join(self.upload_folder, out_name)
            img.save(out_path, "PNG")

        # Preview of result
        iw, ih = img.size
        preview = img.copy()
        if max(iw, ih) > 1400:
            ratio   = 1400 / max(iw, ih)
            preview = img.resize((int(iw * ratio), int(ih * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=92)
        result_b64 = base64.b64encode(buf.getvalue()).decode()

        return {
            "success":        True,
            "result_filename": out_name,
            "image_b64":      result_b64,
            "preview_width":  preview.width,
            "preview_height": preview.height,
        }
