# hcml_processor.py
# Main document processor for HCML version97600

import json
import os
from hcml_core   import build_cipher_map, encrypt_text, decrypt_text
from hcml_parser import (
    is_valid_open_tag, is_valid_close_tag,
    parse_attributes, DEFAULTS
)

CLASSES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "HCML_Classes.json"
)


class HCMLProcessor:
    def __init__(self, chinese_chars: list):
        self.chinese_chars = chinese_chars
        self.classes: dict = {}
        self._load_classes()

    # ─── Class persistence ────────────────────────────────────────────────────
    def _load_classes(self):
        """Load HCML_Classes.json if it exists."""
        if os.path.exists(CLASSES_FILE):
            try:
                with open(CLASSES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Normalize: remove 'class' key from stored values
                for name, attrs in data.items():
                    clean = dict(attrs)
                    clean.pop("class", None)
                    # Convert tokens from list (JSON) — already list, fine
                    self.classes[name] = clean
            except Exception:
                pass  # Corrupt JSON — start fresh

    def _save_classes(self):
        """Persist classes to HCML_Classes.json."""
        try:
            # Build saveable dict (add class name back for readability)
            out = {}
            for name, attrs in self.classes.items():
                entry = dict(attrs)
                entry["class"] = name
                # Put class first for readability
                ordered = {"class": name}
                ordered.update({k: v for k, v in entry.items() if k != "class"})
                out[name] = ordered
            with open(CLASSES_FILE, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ─── Public entry ─────────────────────────────────────────────────────────
    def process(self, text: str) -> str:
        result = []
        i      = 0
        n      = len(text)

        while i < n:
            tag_info = is_valid_open_tag(text, i)

            if tag_info is not None:
                tag_type, after_open, inner = tag_info
                attrs, class_name = parse_attributes(inner, self.classes)

                # Save/update class if named
                if class_name:
                    self._save_class(class_name, attrs)
                    self._save_classes()  # persist to JSON

                close_info = self._find_close(text, after_open, tag_type)

                if close_info is None:
                    body          = text[after_open:]
                    after_close   = n
                    close_tag_str = ""
                else:
                    close_start, after_close = close_info
                    body          = text[after_open:close_start]
                    close_tag_str = text[close_start:after_close]

                open_tag_str   = text[i:after_open]
                processed_body = self._process_body(body, attrs, tag_type)
                mode           = attrs.get("mode", "")

                if mode == "#":
                    result.append(processed_body)
                else:
                    result.append(open_tag_str)
                    result.append(processed_body)
                    if close_tag_str:
                        result.append(close_tag_str)

                i = after_close
            else:
                result.append(text[i])
                i += 1

        return "".join(result)

    # ─── Find matching close tag ──────────────────────────────────────────────
    def _find_close(self, text: str, start: int, tag_type: str):
        i = start
        n = len(text)
        while i < n:
            close = is_valid_close_tag(text, i)
            if close is not None:
                ctype, after = close
                if ctype == tag_type:
                    return (i, after)
                else:
                    i += 1
                    continue
            i += 1
        return None

    # ─── Process body with token logic ───────────────────────────────────────
    def _process_body(self, body: str, attrs: dict, tag_type: str) -> str:
        tokens     = attrs.get("tokens", DEFAULTS["tokens"])
        cipher_map = build_cipher_map(self.chinese_chars, attrs)

        if not tokens:
            return body

        result = []
        i      = 0
        n      = len(body)
        active = False

        while i < n:
            matched_token = self._match_token(body, i, tokens)

            if matched_token is not None:
                result.append(matched_token)
                i += len(matched_token)
                active = not active
                continue

            if active:
                run_start = i
                while i < n and self._match_token(body, i, tokens) is None:
                    i += 1
                segment = body[run_start:i]
                if tag_type == "E":
                    result.append(encrypt_text(segment, cipher_map))
                else:
                    result.append(decrypt_text(segment, cipher_map))
            else:
                result.append(body[i])
                i += 1

        return "".join(result)

    # ─── Token matching ───────────────────────────────────────────────────────
    def _match_token(self, text: str, pos: int, tokens: list):
        for tok in tokens:
            if tok and text[pos:pos + len(tok)] == tok:
                return tok
        return None

    # ─── Class registry ───────────────────────────────────────────────────────
    def _save_class(self, name: str, attrs: dict):
        """
        Save or update a named class.
        Stores all attrs EXCEPT 'class' itself.
        mode='!' is not stored (it's a per-use random key, not a setting).
        """
        saved = {}
        for k, v in attrs.items():
            if k == "class":
                continue
            if k == "mode" and v == "!":
                # Don't persist the random-key mode — but DO persist mode="#"
                saved[k] = ""
            else:
                saved[k] = v
        self.classes[name] = saved
