"""Safe resume normalization that never adds or invents content.

The repair step only changes presentation details: section labels, bullet
markers, whitespace, and a small set of product-name capitalizations. It does
not rewrite claims, metrics, dates, or achievements.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from resume_formatter import (
    ALIASES,
    BULLET_RE,
    GENERIC_HEADER_TITLES,
    clean_text,
    expand_heading_line,
    normalize_heading,
)


PRODUCT_NAMES = {
    "chatgpt": "ChatGPT",
    "javascript": "JavaScript",
    "powerpoint": "PowerPoint",
    "ppt": "PowerPoint",
}


def _normalize_product_names(value: str) -> tuple[str, set[str]]:
    found: set[str] = set()
    for source, target in PRODUCT_NAMES.items():
        updated = re.sub(rf"\b{re.escape(source)}\b", target, value, flags=re.I)
        if updated != value:
            found.add(target)
        value = updated
    return value, found


def _change(label: str, detail: str, count: int = 0) -> dict[str, Any]:
    return {"label": label, "detail": detail, "count": count}


def repair_resume(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Return normalized resume text and a human-readable change summary."""

    output: list[str] = []
    heading_changes: Counter[str] = Counter()
    dropped_titles: Counter[str] = Counter()
    product_changes: Counter[str] = Counter()
    bullet_markers = 0
    spacing_changes = 0
    previous_blank = False
    in_header = True

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if output and not previous_blank:
                output.append("")
            previous_blank = True
            continue
        previous_blank = False

        for part in expand_heading_line(stripped):
            canonical = ALIASES.get(normalize_heading(part))
            if canonical:
                in_header = False
                if part != canonical:
                    heading_changes[f"{part} -> {canonical}"] += 1
                output.append(canonical)
                continue

            if in_header and part.lower().rstrip(":：") in GENERIC_HEADER_TITLES:
                dropped_titles[part] += 1
                continue

            match = BULLET_RE.match(part)
            if match:
                marker = part[: match.start(1)].strip()
                content = clean_text(match.group(1))
                content, names = _normalize_product_names(content)
                product_changes.update(names)
                if marker != "•":
                    bullet_markers += 1
                if content != match.group(1):
                    spacing_changes += 1
                output.append(f"• {content}")
                continue

            cleaned = clean_text(part)
            cleaned, names = _normalize_product_names(cleaned)
            product_changes.update(names)
            if cleaned != part:
                spacing_changes += 1
            output.append(cleaned)

    while output and output[0] == "":
        output.pop(0)
    while output and output[-1] == "":
        output.pop()

    fixed_text = "\n".join(output)
    changes: list[dict[str, Any]] = []

    if dropped_titles:
        labels = ", ".join(sorted(dropped_titles))
        changes.append(_change("Removed generic title lines", labels, sum(dropped_titles.values())))

    if heading_changes:
        examples = "; ".join(list(heading_changes)[:5])
        if len(heading_changes) > 5:
            examples += "; ..."
        changes.append(
            _change(
                "Standardized section headings",
                examples,
                sum(heading_changes.values()),
            )
        )

    if bullet_markers:
        changes.append(
            _change(
                "Normalized bullet markers",
                f"Converted {bullet_markers} bullet marker(s) to •.",
                bullet_markers,
            )
        )

    if spacing_changes:
        changes.append(
            _change(
                "Cleaned spacing",
                f"Removed extra spaces or line-break noise from {spacing_changes} line(s).",
                spacing_changes,
            )
        )

    if product_changes:
        changes.append(
            _change(
                "Standardized tool names",
                "Corrected capitalization for " + ", ".join(sorted(product_changes)) + ".",
                sum(product_changes.values()),
            )
        )

    if not changes:
        changes.append(
            _change(
                "No safe text changes needed",
                "The text was already clean. The selected template applies the layout and print formatting.",
            )
        )

    return fixed_text, changes
