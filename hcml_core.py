# hcml_core.py
# Chinese Coder 97600 — HCML version97600
# Core encryption/decryption algorithm

import os
import random


def load_chinese_chars(filepath: str) -> list[str]:
    """Load the 97600 Chinese characters from file."""
    with open(filepath, "r", encoding="utf-8") as f:
        chars = list(f.read())
    # Remove newlines/whitespace that might be in the file
    chars = [c for c in chars if c.strip()]
    return chars


def _make_charset(chinese_chars: list[str], count) -> list[str]:
    """
    Extract a subset of Chinese chars based on count parameter.
    count can be:
      - int  → chars[0:count]
      - tuple(start, end) → chars[start:end]
    """
    if isinstance(count, tuple):
        start, end = count
        return chinese_chars[start:end]
    else:
        return chinese_chars[0:int(count)]


def _apply_way_ordering(charset: list[str], way: str) -> list[str]:
    """
    Apply ordering/stride to charset based on 'way' parameter.
    Handles: +, -, %n
    Returns re-ordered charset.
    """
    way = str(way).strip()

    if way == "+":
        return charset[:]

    elif way == "-":
        return charset[::-1]

    elif way.startswith("%"):
        try:
            n = int(way[1:])
            if n < 1:
                return charset[:]
        except ValueError:
            return charset[:]
        # stride: interleave groups
        result = []
        for offset in range(n):
            result.extend(charset[offset::n])
        return result

    else:
        return charset[:]


def _get_multiplier(way: str) -> int:
    """Extract *n multiplier from way string. Default 1."""
    way = str(way).strip()
    if way.startswith("*"):
        try:
            n = int(way[1:])
            return max(1, min(5, n))
        except ValueError:
            return 1
    return 1


def build_cipher_map(chinese_chars: list[str], params: dict) -> dict:
    """
    Build a mapping from every supported Unicode codepoint
    to one (or more) Chinese characters.

    The mapping is deterministic given key + count + way.
    key shifts the starting index in the charset (with modulo).
    """
    count = params.get("count", 3000)
    way   = params.get("way", "+")
    key   = params.get("key", 0)

    charset = _make_charset(chinese_chars, count)

    # Split way into ordering part and multiplier part
    # e.g. way might be "+" or "-" or "%2" or "*3"
    # They are separate attributes in the spec but we handle both
    ordering_way = way
    multiplier   = 1
    if isinstance(way, str) and way.startswith("*"):
        multiplier   = _get_multiplier(way)
        ordering_way = "+"  # default ordering when only * is given

    charset = _apply_way_ordering(charset, ordering_way)

    if len(charset) == 0:
        raise ValueError("Charset is empty — check count parameter.")

    # key shifts the base index
    # We use a simple deterministic shuffle seeded by key
    # so that key=23 and key=24 give different maps
    rng = random.Random(int(key))
    shuffled = charset[:]
    rng.shuffle(shuffled)

    # Build the map: codepoint → [chinese_char * multiplier]
    # We iterate over all printable Unicode planes that we care about.
    # The practical approach: map on demand during encrypt,
    # using index = (ord(char) + key) % len(shuffled)
    # This gives a unique, reversible map as long as len(shuffled) is large.

    return {
        "shuffled": shuffled,
        "multiplier": multiplier,
        "key": int(key),
    }


def _char_to_chinese(char: str, cipher_map: dict) -> str:
    """Map a single character to its Chinese encoding."""
    shuffled   = cipher_map["shuffled"]
    multiplier = cipher_map["multiplier"]
    key        = cipher_map["key"]

    n = len(shuffled)
    idx = (ord(char) + abs(key)) % n
    ch  = shuffled[idx]
    return ch * multiplier


def _chinese_to_char(chinese_block: str, cipher_map: dict, multiplier: int) -> str:
    """Reverse: given a block of multiplier Chinese chars, return original char."""
    shuffled = cipher_map["shuffled"]
    key      = cipher_map["key"]
    n        = len(shuffled)

    # Take first char of the block (all are the same in *n mode)
    ch  = chinese_block[0]
    try:
        idx = shuffled.index(ch)
    except ValueError:
        return "?"

    code = (idx - abs(key)) % n
    try:
        return chr(code)
    except (ValueError, OverflowError):
        return "?"


# ─── Special sentinel for newline and space ───────────────────────────────────
# We encode \n and space as regular characters (they have ord values).
# They will be encrypted just like any other character.
# The encrypted output is stored as a single line, so we need a way
# to distinguish encoded \n from literal \n in the output file.
# Strategy: the encrypted portion is written inline; the structure
# (tags, non-encrypted text) keeps its newlines.
# Encrypted segments are contiguous Chinese characters on one line.

def encrypt_text(text: str, cipher_map: dict) -> str:
    """Encrypt a string to Chinese characters (single line output)."""
    result = []
    for char in text:
        result.append(_char_to_chinese(char, cipher_map))
    return "".join(result)


def decrypt_text(chinese_text: str, cipher_map: dict) -> str:
    """Decrypt a string of Chinese characters back to original text."""
    multiplier = cipher_map["multiplier"]
    result     = []
    i          = 0
    while i < len(chinese_text):
        block = chinese_text[i : i + multiplier]
        if len(block) == 0:
            break
        result.append(_chinese_to_char(block, cipher_map, multiplier))
        i += multiplier
    return "".join(result)
