# hcml_parser.py
# Parses <E ...> and <D ...> tags and their attributes.

import re

# ─── Default attribute values ─────────────────────────────────────────────────
DEFAULTS = {
    "class":  "",
    "count":  3000,
    "key":    0,
    "way":    "+",
    "mode":   "",
    "tokens": ["{", "}"],
}


def parse_count(raw: str):
    raw = raw.strip()
    if ":" in raw:
        parts = raw.split(":", 1)
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return DEFAULTS["count"]
    try:
        return int(raw)
    except ValueError:
        return DEFAULTS["count"]


def parse_key(raw: str):
    raw = raw.strip()
    try:
        return int(raw)
    except ValueError:
        return DEFAULTS["key"]


def parse_tokens(raw: str) -> list:
    raw = raw.strip()
    found = re.findall(r'"([^"]*)"', raw)
    if not found:
        found = re.findall(r"'([^']*)'", raw)
    return found


def _extract_raw_attrs(tag_inner: str) -> dict:
    """
    Extract attr=value pairs from tag interior.
    Attr must be preceded by whitespace (or start of string).
    Supports: attr="val", attr='val', attr=[...]
    Returns dict with last-value-wins for duplicates.
    """
    raw = {}
    # We build the pattern as bytes-like string to avoid quoting hell
    # Pattern: (whitespace or ^)(word)(=)("..." or '...' or [...])
    i = 0
    n = len(tag_inner)

    while i < n:
        # Skip whitespace
        while i < n and tag_inner[i] in ' \t\n\r':
            i += 1
        if i >= n:
            break

        # Try to read a word (attr name candidate)
        if not (tag_inner[i].isalpha() or tag_inner[i] == '_'):
            i += 1
            continue

        word_start = i
        while i < n and (tag_inner[i].isalnum() or tag_inner[i] == '_'):
            i += 1
        word = tag_inner[word_start:i]

        # Skip optional spaces
        while i < n and tag_inner[i] in ' \t':
            i += 1

        # Must be followed by =
        if i >= n or tag_inner[i] != '=':
            # Not attr=value — skip; but don't advance too far
            continue

        i += 1  # skip =

        # Skip optional spaces after =
        while i < n and tag_inner[i] in ' \t':
            i += 1

        if i >= n:
            break

        # Read value: "...", '...', or [...]
        ch = tag_inner[i]
        if ch == '"':
            i += 1
            val_start = i
            while i < n and tag_inner[i] != '"':
                i += 1
            val = tag_inner[val_start:i]
            if i < n:
                i += 1  # skip closing "
            raw[word] = val

        elif ch == "'":
            i += 1
            val_start = i
            while i < n and tag_inner[i] != "'":
                i += 1
            val = tag_inner[val_start:i]
            if i < n:
                i += 1
            raw[word] = val

        elif ch == '[':
            bracket_start = i
            depth = 0
            while i < n:
                if tag_inner[i] == '[':
                    depth += 1
                elif tag_inner[i] == ']':
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            raw[word] = tag_inner[bracket_start:i]

        else:
            # Unquoted value — not valid per spec, skip
            pass

    return raw


def parse_attributes(tag_inner: str, classes: dict) -> tuple:
    """
    Parse tag interior, return (attrs_dict, class_name).
    """
    raw_attrs = _extract_raw_attrs(tag_inner)

    result = dict(DEFAULTS)

    # Load class first
    class_name = raw_attrs.get("class", "").strip()
    if class_name:
        result["class"] = class_name
        if class_name in classes:
            for k, v in classes[class_name].items():
                result[k] = v

    # Apply explicit attrs (override class)
    for attr_name, val_str in raw_attrs.items():
        if attr_name == "class":
            continue
        if attr_name == "count":
            result["count"] = parse_count(val_str)
        elif attr_name == "key":
            result["key"] = parse_key(val_str)
        elif attr_name == "way":
            result["way"] = val_str.strip()
        elif attr_name == "mode":
            result["mode"] = val_str.strip()
        elif attr_name == "tokens":
            result["tokens"] = parse_tokens("[" + val_str + "]" if not val_str.startswith("[") else val_str)
        # Unknown attrs silently ignored

    # Handle mode="!" — randomize key
    if result["mode"] == "!":
        import random
        result["key"] = random.randint(-(10**15), 10**15)

    return result, class_name


def is_valid_open_tag(text: str, pos: int):
    """
    Check if position pos starts a valid <E or <D tag.
    Returns (tag_type, end_pos, inner_str) or None.
    """
    if pos >= len(text) or text[pos] != "<":
        return None

    i = pos + 1

    if i >= len(text):
        return None

    # No / (not a closing tag)
    if text[i] == "/":
        return None

    # Must be E or D immediately
    tag_letter = text[i].upper()
    if tag_letter not in ("E", "D"):
        return None

    i += 1

    # After E/D must be >, whitespace, or end — NOT another alnum char
    if i < len(text) and (text[i].isalnum() or text[i] == '_'):
        return None

    # Scan for closing > (respecting quotes and brackets)
    depth_bracket = 0
    in_quote = None
    j = i

    while j < len(text):
        c = text[j]
        if in_quote:
            if c == in_quote:
                in_quote = None
        elif c in ('"', "'"):
            in_quote = c
        elif c == "[":
            depth_bracket += 1
        elif c == "]":
            depth_bracket -= 1
        elif c == ">" and depth_bracket == 0:
            inner = text[i:j]
            end = j + 1
            return (tag_letter, end, inner)
        j += 1

    return None


def is_valid_close_tag(text: str, pos: int):
    """
    Check if position pos starts </E> or </D>.
    Returns (tag_type, end_pos) or None.
    """
    if text[pos:pos+2] != "</":
        return None
    i = pos + 2
    if i >= len(text):
        return None
    tag_letter = text[i].upper()
    if tag_letter not in ("E", "D"):
        return None
    i += 1
    if i < len(text) and text[i] == ">":
        return (tag_letter, i + 1)
    return None
