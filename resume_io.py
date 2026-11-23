"""Resume file input helpers for TXT, Markdown, DOCX, and PDF."""

from __future__ import annotations

import os
import re
import subprocess
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

PDF_APPLESCRIPT = r'''
use framework "Foundation"
use framework "PDFKit"
set p to "__RESUME_PATH__"
set u to current application's NSURL's fileURLWithPath:p
set d to current application's PDFDocument's alloc()'s initWithURL:u
if d is missing value then error "Could not open PDF"
set outText to ""
set n to d's pageCount() as integer
repeat with i from 0 to (n - 1)
	set pg to d's pageAtIndex:i
	set raw to pg's valueForKey:"string"
	set s to raw as text
	set outText to outText & linefeed & s & linefeed
end repeat
return outText
'''


def extract_docx_text(path: str | Path) -> str:
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml")
    root = ET.fromstring(document)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{W_NS}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{W_NS}t")).strip()
        if not text:
            continue
        properties = paragraph.find(f"{W_NS}pPr")
        is_bullet = properties is not None and properties.find(f"{W_NS}numPr") is not None
        paragraphs.append(f"• {text}" if is_bullet else text)
    text = "\n".join(paragraphs)
    text = re.sub(r"([•●▪◦])(?=\S)", r"\1 ", text)
    text = re.sub(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\n\s*((?:19|20)\d{2})",
        r"\1 \2",
        text,
        flags=re.I,
    )
    return text


def extract_pdf_text(path: str | Path) -> str:
    safe_path = str(path).replace("\\", "\\\\").replace('"', '\\"')
    script = PDF_APPLESCRIPT.replace("__RESUME_PATH__", safe_path)
    result = subprocess.run(
        ["osascript", "-"],
        input=script,
        text=True,
        capture_output=True,
        timeout=90,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "PDF text extraction failed"
        raise RuntimeError(detail)
    lines: list[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r"(?:page\s*)?\d{1,3}", stripped, flags=re.I):
            continue
        if stripped.lower() == "capd.mit.edu":
            continue
        if "MIT Career Advising & Professional Development" in stripped:
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_resume_text(path: str | Path) -> str:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix in {".txt", ".md", ".markdown", ".text"}:
        return source.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        return extract_docx_text(source)
    if suffix == ".pdf":
        return extract_pdf_text(source)
    raise ValueError("Unsupported file type. Use .txt, .md, .docx, or .pdf.")
