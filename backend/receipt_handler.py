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
try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    _CV2_AVAILABLE = False
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

# Monospace bold fonts in priority order (Mac, Linux, Windows).
# Each entry is (path, ttc_index) — ttc_index is 0 for plain .ttf files.
# Courier New Bold is the closest match for HP thermal/dot-matrix receipt fonts:
# digit shapes (0, 6, 9) and overall proportions align well with printed receipts.
FONT_PATHS = [
    ("/System/Library/Fonts/Supplemental/Courier New Bold.ttf",      0),  # Mac
    ("/Library/Fonts/Courier New Bold.ttf",                          0),  # Mac (alt)
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf", 0),  # Linux
    ("/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",          0),  # Linux (alt)
    (r"C:\Windows\Fonts\courbd.ttf",                                 0),  # Windows
]


def _find_font():
    """Return (path, ttc_index) for the first available font, or (None, 0)."""
    for p, idx in FONT_PATHS:
        if os.path.isfile(p):
            return p, idx
    return None, 0


_FONT_PATH, _FONT_IDX = _find_font()


class ReceiptHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder

    # ------------------------------------------------------------------ #
    #  Font helpers
    # ------------------------------------------------------------------ #

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        if _FONT_PATH:
            try:
                return ImageFont.truetype(_FONT_PATH, size, index=_FONT_IDX)
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
            font = ImageFont.truetype(_FONT_PATH, mid, index=_FONT_IDX)
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
        """Grayscale → CLAHE → Otsu binarisation.

        CLAHE equalises contrast *locally*, so faint rows that sit under a
        faded stamp or watermark (e.g. the "Rate" line on HP fuel receipts)
        survive binarisation. A global contrast+threshold pass — which this
        replaced — wiped those rows out entirely, dropping them from OCR.
        """
        if not _CV2_AVAILABLE:
            # Fallback when OpenCV is unavailable: contrast boost + global threshold.
            gray = img.convert("L")
            gray = ImageEnhance.Contrast(gray).enhance(3.0)
            gray = ImageEnhance.Sharpness(gray).enhance(2.0)
            arr = np.array(gray, dtype=np.float32)
            thresh = float(min(arr.mean() * 0.88, 200))
            return gray.point(lambda p: 255 if p > thresh else 0)

        arr = np.array(img.convert("L"))
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        arr = clahe.apply(arr)
        _, binary = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(binary)

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

        # Group words into visual lines by vertical centre. A fixed pixel "band"
        # splits a row whenever the label and value glyphs have slightly different
        # centres and straddle a band boundary (e.g. "Rate" vs ">-Rs.103.76", which
        # land 10px apart) — orphaning the value. Instead, cluster greedily with a
        # gap threshold derived from the median glyph height, so it tolerates
        # within-row baseline jitter and auto-scales to the scan's resolution.
        med_h = sorted(w["height"] for w in words)[len(words) // 2] if words else 20
        gap = max(8, int(med_h * 0.7))
        sorted_lines = []
        cur, cur_center = [], None
        for w in sorted(words, key=lambda w: w["top"] + w["height"] / 2):
            c = w["top"] + w["height"] / 2
            if cur and abs(c - cur_center) > gap:
                sorted_lines.append(cur)
                cur = []
            cur.append(w)
            cur_center = sum(x["top"] + x["height"] / 2 for x in cur) / len(cur)
        if cur:
            sorted_lines.append(cur)
        sorted_lines.sort(key=lambda ws: min(w["top"] for w in ws))

        fields = []
        pending = []   # label-bearing lines with no detectable colon (rescued below)
        for line in sorted_lines:
            line = sorted(line, key=lambda w: w["left"])

            # Find first word that contains ':'
            colon_idx = None
            for i, w in enumerate(line):
                if ":" in w["text"]:
                    colon_idx = i
                    break

            # Fallback: OCR sometimes misreads ':' as '-' (e.g. "-Rs.103.76").
            # If no colon found, check if a word starts with '-' followed by
            # alphabetic chars — treat it as a misread colon only when the line
            # contains a known field label (avoids false-positives on real hyphens).
            if colon_idx is None:
                label_text_so_far = " ".join(w["text"] for w in line).lower()
                if any(re.search(p, label_text_so_far) for p, _ in KNOWN_FIELDS):
                    for i, w in enumerate(line):
                        t = w["text"]
                        if (t.startswith('-') and len(t) > 1
                                and any(c.isalpha() for c in t[1:4])):
                            line = list(line)
                            line[i] = dict(line[i])
                            line[i]["text"] = ':' + t[1:]
                            colon_idx = i
                            break

            if colon_idx is None:
                # Defer to the colon-column rescue pass below: the colon may have
                # been misread as junk (e.g. "Rate" + ">-Rs.103.76"), so the value
                # is unrecoverable until we know where the value column sits.
                label_join = " ".join(w["text"] for w in line).lower()
                if any(re.search(p, label_join) for p, _ in KNOWN_FIELDS):
                    pending.append(line)
                continue

            field = self._field_from_colon_line(line, colon_idx)
            if field:
                fields.append(field)

        # ── Consensus colon column ──────────────────────────────────────────
        # Every value_bbox[0] is the actual ':' pixel position, so they cluster
        # tightly. Take the median of the densest 20px cluster (ignores indented
        # sub-fields / outliers). This column also drives the rescue pass.
        colon_col = self._consensus_colon_col(fields)

        # ── Rescue pass ─────────────────────────────────────────────────────
        # For label lines whose colon OCR'd as junk, split label vs. value at the
        # colon column and synthesize the field (strips leading junk like ">-").
        if colon_col is not None:
            for line in pending:
                field = self._field_from_column(line, colon_col)
                if field:
                    fields.append(field)
            # Recompute now that rescued fields contribute their own colon x0.
            colon_col = self._consensus_colon_col(fields) or colon_col

        # Snap each value_bbox x0 to the consensus column for clean alignment.
        if colon_col is not None:
            for f in fields:
                if f["value_bbox"] and abs(f["value_bbox"][0] - colon_col) < 50:
                    f["value_bbox"][0] = colon_col

        return fields

    @staticmethod
    def _strip_lead_junk(s: str) -> str:
        """Drop a leading run of non-alphanumeric OCR noise (e.g. '>-', '“-', '*')."""
        return re.sub(r'^[^0-9A-Za-z]+', '', s)

    @staticmethod
    def _consensus_colon_col(fields: list):
        """Median x0 of the densest 20px cluster of value-bbox left edges, or None."""
        x0_list = sorted(f["value_bbox"][0] for f in fields if f["value_bbox"])
        if len(x0_list) < 3:
            return x0_list[len(x0_list) // 2] if x0_list else None
        best_start, best_count = 0, 0
        for v in x0_list:
            count = sum(1 for u in x0_list if abs(u - v) <= 20)
            if count > best_count:
                best_count, best_start = count, v
        cluster = [v for v in x0_list if abs(v - best_start) <= 20]
        return cluster[len(cluster) // 2]

    def _field_from_colon_line(self, line: list, colon_idx: int):
        """Build a field dict from a line where the colon was detected."""
        cw       = line[colon_idx]
        cw_text  = cw["text"]
        colon_pos_in_word = cw_text.index(":")
        before_colon = cw_text[:colon_pos_in_word]    # e.g. "No" or ""
        after_colon  = cw_text[colon_pos_in_word + 1:]  # e.g. "Apr-882977"

        label_parts = [w["text"] for w in line[:colon_idx]]
        if before_colon:
            label_parts.append(before_colon)
        label_text = " ".join(label_parts).strip()
        if not label_text:
            return None

        # Value text — always prefixed with ':' so the span is colon-inclusive
        value_words = line[colon_idx + 1:]
        value_parts = []
        if after_colon:
            value_parts.append(after_colon)
        value_parts += [w["text"] for w in value_words]
        value_text = ":" + " ".join(value_parts).strip()

        # ── Value bbox: starts exactly at the ':' character ─────────────
        if value_words:
            # Case D: standalone colon word — x0 at the ':' token's left.
            x0 = cw["left"]
            y0 = cw["top"]
            x1 = max(w["left"] + w["width"]  for w in value_words)
            y1 = max(w["top"]  + w["height"] for w in value_words)
            value_bbox = [x0, y0, x1, y1]
        elif after_colon:
            # Cases A/B/C: colon is embedded in the word.
            char_w = cw["width"] / max(len(cw_text), 1)
            x0 = int(cw["left"] + char_w * colon_pos_in_word)
            y0 = cw["top"]
            x1 = cw["left"] + cw["width"]
            y1 = cw["top"] + cw["height"]
            value_bbox = [x0, y0, x1, y1]
        else:
            # Lone colon at end of word with no value found
            value_bbox = None

        return self._make_field(label_text, value_text, value_bbox, line)

    def _field_from_column(self, line: list, colon_col: int):
        """Rescue a field by splitting at the consensus colon column.

        Used when the ':' was OCR'd as junk. Words at/after the column form the
        value (leading junk stripped); words before it form the label.
        """
        TOL = 40
        value_words = [w for w in line if w["left"] >= colon_col - TOL]
        label_words = [w for w in line if w["left"] <  colon_col - TOL]
        if not value_words or not label_words:
            return None

        # Drop trailing pure-punctuation noise words (stray '.', '°', '"' left by a
        # faded stamp) so the value box doesn't stretch across empty paper — which
        # would over-erase on inpaint. Keep them if they're all we have.
        while len(value_words) > 1 and not any(c.isalnum() for c in value_words[-1]["text"]):
            value_words.pop()

        label_text = " ".join(w["text"] for w in label_words).strip()
        if not label_text:
            return None

        raw_value = " ".join(w["text"] for w in value_words).strip()
        clean_value = self._strip_lead_junk(raw_value)
        if not clean_value:
            return None
        value_text = ":" + clean_value

        x0 = colon_col
        y0 = min(w["top"] for w in value_words)
        x1 = max(w["left"] + w["width"]  for w in value_words)
        y1 = max(w["top"]  + w["height"] for w in value_words)
        return self._make_field(label_text, value_text, [x0, y0, x1, y1], line)

    def _make_field(self, label_text: str, value_text: str,
                    value_bbox, line: list) -> dict:
        """Assemble a field dict, matching the label to a known field type."""
        # 33rd-percentile height (not median) so a 2-word line (e.g. "Time" +
        # ":16:51:06") doesn't return the larger inflated value.
        heights = sorted(w["height"] for w in line)
        line_height = heights[max(0, len(heights) // 3)] if heights else 20

        field_type = None
        for pattern, name in KNOWN_FIELDS:
            if re.search(pattern, label_text.lower()):
                field_type = name
                break

        return {
            "label":       label_text,
            "field_type":  field_type,
            "value":       value_text,
            "value_bbox":  value_bbox,
            "line_height": line_height,
        }

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

            # Normalize a leading '-' that OCR misread as ':'.
            # Heuristic: starts with '-', followed by 1–3 alphabetic chars
            # (e.g. "-Rs.103.76" → ":Rs.103.76").  Real negative numbers
            # start with '-' followed by a digit, so they are unaffected.
            if (txt.startswith('-') and len(txt) > 1
                    and any(c.isalpha() for c in txt[1:4])):
                txt = ':' + txt[1:]

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
                    if colon_pos > 0:
                        # Label text immediately precedes the colon in the same
                        # OCR word (e.g. "No:Apr-882977") — skip only the label.
                        label_skip = int(char_w * colon_pos)
                        txt        = txt[colon_pos:]
                        x         += label_skip
                        w          = max(w - label_skip, 1)
                    # colon_pos == 0: colon is already at the word's left edge.
                    # txt stays ':value', x stays at the colon position.

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

    def _analyze_global_appearance(self, arr: np.ndarray) -> dict:
        """
        Measure the visual quality of ALL printed text in the receipt image
        and return a single appearance dict used for every edit.

        Analysing the full image avoids the per-bbox sampling failure that
        occurs when the row above a field is background (e.g. Bill No at the
        top of the receipt), which previously produced a wrong (too-light) ink
        colour.

        Returns: { "ink_color": (r,g,b), "blur_sigma": float }
        """
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

        # ── Ink colour ──────────────────────────────────────────────────
        # Use Otsu to separate ink from background globally.
        _, ink_mask = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        ink_pixels = arr[ink_mask > 0]   # all dark pixels in the image

        if len(ink_pixels) >= 50:
            # Median is robust against stamps / noise patches.
            ink_color = tuple(int(v) for v in np.median(ink_pixels, axis=0))
        else:
            ink_color = (20, 20, 20)

        # ── Blur sigma ──────────────────────────────────────────────────
        # Laplacian variance over the ENTIRE image captures average sharpness.
        # We restrict to ink-adjacent pixels so stamps/background don't bias it.
        blur_sigma = 0.7   # safe default for phone-camera receipt scans
        ink_px = int((ink_mask > 0).sum())
        if ink_px > 100:
            # Dilate ink mask to include edge-transition pixels
            kernel = np.ones((3, 3), np.uint8)
            edge_zone = cv2.dilate(ink_mask, kernel, iterations=1)
            lap = cv2.Laplacian(gray, cv2.CV_32F)
            sharpness = float(lap[edge_zone > 0].var()) if edge_zone.any() else 0.0
            # Mapping: sharpness ~5000 → sigma 0.3 (crisp)
            #          sharpness  ~500 → sigma 0.8 (phone scan)
            #          sharpness  ~ 50 → sigma 1.5 (very blurry)
            blur_sigma = float(np.clip(
                2.0 - np.log10(max(sharpness, 1)) * 0.38,
                0.3, 1.8
            ))

        return {"ink_color": ink_color, "blur_sigma": blur_sigma}

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
                     appearance: dict | None = None) -> Image.Image:
        """
        Draw new text into bbox with auto-matched font size.

        If `appearance` is provided (from _analyze_text_appearance) the text
        is rendered with the sampled ink colour and a Gaussian blur whose
        sigma matches the original print+camera blur, so the replacement is
        visually consistent with the rest of the scanned receipt.
        """
        x0, y0, x1, y1 = [int(v) for v in bbox]
        bbox_h = max(y1 - y0, 1)
        size_pct = float(appearance.get("size_pct", 100)) if appearance else 100.0
        global_h = float(appearance.get("text_height", 0)) if appearance else 0.0

        if global_h > 0:
            # Receipt prints one uniform size: size every edit from the global
            # text height, and match the font against a fixed digit reference so
            # sizing is identical regardless of the edit's own glyphs (caps,
            # descenders, slashes). This is what keeps Rate/Date/Bill No the same
            # size as the surrounding print instead of shrinking to their box.
            target_h = max(4, int(global_h * size_pct / 100.0))
            font_size = self._match_font_size("0123456789", target_h)
        else:
            # Legacy path (no global height available): guess from this field's box.
            base_h   = min(bbox_h, line_height) if line_height > 0 else bbox_h
            target_h = max(4, int(base_h * size_pct / 100.0))
            font_size = self._match_font_size(text, int(target_h * 0.90))
        font = self._get_font(font_size)

        ink_color  = appearance["ink_color"]  if appearance else (20, 20, 20)
        blur_sigma = appearance["blur_sigma"] if appearance else 0.6

        # Compute vertical position
        try:
            bb = font.getbbox(text)
            text_h = bb[3] - bb[1]
            y_pos = y0 + (bbox_h - text_h) // 2 - bb[1]
        except Exception:
            y_pos = y0 + 2

        # Render text on a transparent RGBA layer, then blur + composite.
        # This avoids drawing directly on the background, which would paint
        # crisp pixels that look synthetic against a blurry scanned image.
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).text(
            (x0, y_pos), text, font=font, fill=(*ink_color, 255)
        )

        if blur_sigma > 0.25:
            layer_arr = np.array(layer, dtype=np.float32)
            for c in range(4):
                layer_arr[:, :, c] = cv2.GaussianBlur(
                    layer_arr[:, :, c], (0, 0), blur_sigma
                )
            layer = Image.fromarray(np.clip(layer_arr, 0, 255).astype(np.uint8))

        # Apply opacity (user-controllable, default 0.85).
        opacity = float(appearance.get("opacity", 0.85)) if appearance else 0.85
        if opacity < 1.0:
            r, g, b, a = layer.split()
            a = a.point(lambda v: int(v * opacity))
            layer = Image.merge("RGBA", (r, g, b, a))

        base = img.convert("RGBA")
        base.paste(layer, mask=layer.split()[3])
        return base.convert("RGB")

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

        # Normalize colon-starting span x0 to the consensus colon column and
        # enrich spans with line_height from the matching field so that
        # span-click edits use the same font sizing as field-panel edits.
        colon_col = None
        if fields:
            x0s = [f["value_bbox"][0] for f in fields if f["value_bbox"]]
            if x0s:
                colon_col = sorted(x0s)[len(x0s) // 2]
        if colon_col is not None or fields:
            for s in all_spans:
                if not s["text"].startswith(":"):
                    continue
                # Snap x0 to the colon column
                if colon_col is not None and abs(s["bbox"][0] - colon_col) < 50:
                    delta = colon_col - s["bbox"][0]
                    s["bbox"][0] += delta
                    s["bbox"][2] -= delta
                # Copy line_height from the closest field on the same Y band
                best_f, best_dy = None, 999
                for f in fields:
                    if not f["value_bbox"]:
                        continue
                    dy = abs(f["value_bbox"][1] - s["bbox"][1])
                    if dy < best_dy:
                        best_dy, best_f = dy, f
                if best_f and best_dy < 20:
                    s["line_height"] = best_f["line_height"]

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

        # Global text height — the single printed font height of the receipt.
        # Thermal/dot-matrix receipts print every line at one size, so the median
        # of high-confidence word-box heights is a far more reliable size target
        # than any individual field's (noisy) OCR box. Used to render ALL edits at
        # a consistent size instead of per-field guesses. See _render_text.
        hc = sorted(s["height"] for s in all_spans if s["conf"] >= 40)
        if len(hc) >= 3:
            text_height = hc[len(hc) // 2]                 # median
        elif all_spans:
            text_height = sorted(s["height"] for s in all_spans)[len(all_spans) // 2]
        else:
            text_height = 0

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
            "text_height":   text_height,
            "lang":          lang,
            "font_available": _FONT_PATH is not None,
        }

    def process_edits(self, filepath: str, edits: list,
                      output_format: str = "pdf",
                      appearance_settings: dict | None = None) -> dict:
        """
        Apply edits to the original image.

        edits: [{ bbox:[x0,y0,x1,y1], new_text:str, line_height:float }, ...]

        appearance_settings (all optional, user-supplied overrides):
          opacity     : float 0.0–1.0  — text visibility (default: 0.85)
          blur        : float 0.0–3.0  — stroke softness; 0 = crisp (default: auto)
          brightness  : int  -50–+50   — ink lightness offset (default: 0)
          text_height : int            — receipt's global printed text height in px.
                        When provided, every edit renders at this single size
                        (× per-edit size_pct) instead of guessing from each
                        field's noisy OCR box. See upload_and_scan / _render_text.
        """
        path = os.path.join(self.upload_folder, os.path.basename(filepath))
        if not os.path.exists(path):
            raise FileNotFoundError(f"Receipt image not found: {filepath}")

        img = Image.open(path).convert("RGB")

        # Analyse the full receipt once for baseline ink colour + blur.
        appearance = self._analyze_global_appearance(np.array(img))

        # Apply user overrides on top of auto-detected values.
        s = appearance_settings or {}
        if "opacity" in s:
            appearance["opacity"] = float(np.clip(s["opacity"], 0.0, 1.0))
        else:
            appearance.setdefault("opacity", 0.85)
        if "blur" in s:
            appearance["blur_sigma"] = float(np.clip(s["blur"], 0.0, 3.0))
        if "brightness" in s:
            offset = int(np.clip(s["brightness"], -50, 50))
            appearance["ink_color"] = tuple(
                int(np.clip(c + offset, 0, 255))
                for c in appearance["ink_color"]
            )
        if s.get("text_height"):
            appearance["text_height"] = int(s["text_height"])

        for edit in edits:
            bbox      = edit["bbox"]
            new_text  = edit.get("new_text") or ""
            line_h    = int(edit.get("line_height") or 20)

            if new_text == "":
                continue

            iw, ih = img.size
            pbbox = [
                max(0, bbox[0] - 3),
                max(0, bbox[1] - 4),
                min(iw, bbox[2] + 5),
                min(ih, bbox[3] + 4),
            ]

            # Per-edit size override: clone global appearance and inject size_pct.
            edit_appearance = dict(appearance)
            edit_appearance["size_pct"] = float(edit.get("size_pct", 100))

            # Apply per-edit bbox trim (T/B/L/R as % of bbox dimensions).
            # Positive = move that edge inward (shrink); negative = expand.
            trim = edit.get("bbox_trim") or {}
            if trim:
                bw = max(bbox[2] - bbox[0], 1)
                bh = max(bbox[3] - bbox[1], 1)
                bbox = [
                    bbox[0] + int(bw * float(trim.get("left",   0)) / 100),
                    bbox[1] + int(bh * float(trim.get("top",    0)) / 100),
                    bbox[2] - int(bw * float(trim.get("right",  0)) / 100),
                    bbox[3] - int(bh * float(trim.get("bottom", 0)) / 100),
                ]
                # Recalculate pbbox from adjusted bbox
                iw, ih = img.size
                pbbox = [
                    max(0, bbox[0] - 3),
                    max(0, bbox[1] - 4),
                    min(iw, bbox[2] + 5),
                    min(ih, bbox[3] + 4),
                ]

            arr      = np.array(img)
            bg_color = self._sample_background(arr, pbbox)
            img = self._inpaint_bbox(img, pbbox, bg_color)
            img = self._render_text(img, bbox, new_text, line_h, edit_appearance)

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
