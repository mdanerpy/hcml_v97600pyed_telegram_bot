#!/usr/bin/env python3
# hcml.py — Hanzi Cipher Markup Language (HCML)
#
# Usage:
#   python hcml.py "D:\path\to\file.txt"
#   python hcml.py "D:\path\to\file.json"
#   python hcml.py "D:\path\to\file.html"
#   python hcml.py          ← interactive mode
#
# Output: same filename + .hcml extension (no -C suffix)
# Supported input: any text-based file (txt, json, xml, html, js, css, py, ...)

import sys
import os

from hcml_core      import load_chinese_chars
from hcml_processor import HCMLProcessor, CLASSES_FILE

CHINESE_CHARS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Characters_Chinese_97600.txt"
)

# Text-based file extensions that are supported
TEXT_EXTENSIONS = {
    ".txt", ".json", ".xml", ".html", ".htm", ".js", ".ts",
    ".css", ".scss", ".less", ".py", ".csv", ".yaml", ".yml",
    ".ini", ".cfg", ".conf", ".md", ".rst", ".log", ".sql",
    ".hcml", ".htcc", ".env", ".bat", ".sh", ".toml",
}


def make_output_path(input_path: str) -> str:
    """
    Given  D:\\folder\\file.txt   →  D:\\folder\\file.txt.hcml
    Given  D:\\folder\\data.json  →  D:\\folder\\data.json.hcml
    The original extension is kept, .hcml is appended.
    """
    return os.path.abspath(input_path) + ".hcml"


def is_supported(input_path: str) -> bool:
    """Check if the file extension is a known text format."""
    _, ext = os.path.splitext(input_path.lower())
    return ext in TEXT_EXTENSIONS


def process_file(input_path: str):
    input_path = input_path.strip().strip('"').strip("'")

    # ── Chinese chars ─────────────────────────────────────────────────────────
    if not os.path.exists(CHINESE_CHARS_FILE):
        print(f"[ERROR] Characters file not found:\n  {CHINESE_CHARS_FILE}")
        sys.exit(1)

    print(f"[•] Loading Chinese characters ...")
    chinese_chars = load_chinese_chars(CHINESE_CHARS_FILE)
    print(f"[•] {len(chinese_chars)} characters loaded.")

    # ── Input file ────────────────────────────────────────────────────────────
    if not os.path.exists(input_path):
        print(f"[ERROR] File not found:\n  {input_path}")
        sys.exit(1)

    if not is_supported(input_path):
        _, ext = os.path.splitext(input_path)
        print(f"[WARNING] Extension '{ext}' is not in the known list, but will try anyway.")

    print(f"[•] Classes file : {CLASSES_FILE}")
    print(f"[•] Processing   : {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # ── Process ───────────────────────────────────────────────────────────────
    processor = HCMLProcessor(chinese_chars)
    output    = processor.process(content)

    if processor.classes:
        print(f"[•] Active classes: {list(processor.classes.keys())}")

    # ── Write output ──────────────────────────────────────────────────────────
    output_path = make_output_path(input_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"[✓] Saved to: {output_path}")


def interactive():
    print("=" * 55)
    print("  Hanzi Cipher Markup Language — HCML")
    print("=" * 55)
    print()
    print("Supported formats: txt, json, xml, html, js, css, py ...")
    print()
    path = input("Enter file path: ").strip().strip('"').strip("'")
    if not path:
        print("[ERROR] No path given.")
        sys.exit(1)
    process_file(path)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_file(sys.argv[1])
    else:
        interactive()
