"""Resume rebuilding and formatting based on general handbook layout principles.

Three templates are modeled on the layout patterns in the extracted
Career-Handbook-2019 PDF:
- masters: page 34 sample (clean master's/standard layout)
- phd: page 36 sample (formal research/PhD layout)
- technical: page 37 sample (summary + skills + research/publications)

The formatter preserves the user's facts. It cleans labels, normalizes
headings, and creates a print-ready HTML document; it does not invent
metrics or experience.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUBRIC = json.loads((ROOT / "rubric.json").read_text(encoding="utf-8"))
ALIASES = {key.upper(): value for key, value in RUBRIC["section_aliases"].items()}
HEADING_KEYS = sorted(ALIASES, key=len, reverse=True)

BULLET_RE = re.compile(r"^\s*(?:[•●▪◦*\-–—]|\d+[.)])\s+(.*\S)\s*$")
DATE_TOKEN = (
    r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+)?"
    r"(?:19|20)\d{2}(?:[./年-]\d{1,2}月?)?"
)
DATE_RANGE = rf"{DATE_TOKEN}(?:\s*[-–—]\s*(?:{DATE_TOKEN}|Present))?"
DATE_TAIL_RE = re.compile(rf"^(.*?)(?:\s+|\s*[|•]\s*)({DATE_RANGE})\s*$", re.I)
DATE_LEAD_RE = re.compile(rf"^({DATE_RANGE})\s+(.+)$", re.I)
PLACEHOLDER_RE = re.compile(r"\[\[(.+?)\]\]")

TEMPLATES: dict[str, dict[str, Any]] = {
    "masters": {
        "label": "Master's / standard (page 34)",
        "font": '"Helvetica Neue", Arial, sans-serif',
        "serif": False,
        "section_case": "uppercase",
        "order": [
            "PROFILE",
            "EDUCATION",
            "EXPERIENCE",
            "RESEARCH",
            "TEACHING",
            "PROJECTS",
            "LEADERSHIP",
            "SERVICE",
            "PUBLICATIONS",
            "AWARDS",
            "SKILLS",
            "ACTIVITIES",
            "INTERESTS",
        ],
        "labels": {
            "PROFILE": "Profile",
            "AWARDS": "Awards",
            "SERVICE": "Service",
            "PUBLICATIONS": "Publications",
        },
    },
    "phd": {
        "label": "PhD / research (page 36)",
        "font": 'Georgia, "Times New Roman", serif',
        "serif": True,
        "section_case": "title",
        "order": [
            "PROFILE",
            "EDUCATION",
            "EXPERIENCE",
            "RESEARCH",
            "TEACHING",
            "AWARDS",
            "SERVICE",
            "PUBLICATIONS",
            "PROJECTS",
            "SKILLS",
            "ACTIVITIES",
            "INTERESTS",
        ],
        "labels": {
            "PROFILE": "Summary",
            "AWARDS": "Fellowships and Awards",
            "SERVICE": "Professional and Public Service",
            "PUBLICATIONS": "Publications and Conferences",
        },
    },
    "technical": {
        "label": "Technical / PhD (page 37)",
        "font": '"Helvetica Neue", Arial, sans-serif',
        "serif": False,
        "section_case": "uppercase",
        "order": [
            "PROFILE",
            "EDUCATION",
            "SKILLS",
            "EXPERIENCE",
            "RESEARCH",
            "TEACHING",
            "PROJECTS",
            "AWARDS",
            "PUBLICATIONS",
            "SERVICE",
            "ACTIVITIES",
            "INTERESTS",
        ],
        "labels": {
            "PROFILE": "Summary",
            "AWARDS": "Honors and Awards",
            "SERVICE": "Service",
            "PUBLICATIONS": "Journal Publications",
        },
    },
}

PLAIN_SECTIONS = {"PUBLICATIONS", "AWARDS", "SKILLS", "ACTIVITIES", "INTERESTS", "SERVICE"}
GENERIC_HEADER_TITLES = {
    "resume",
    "cv",
    "curriculum vitae",
    "personal resume",
    "resume sample",
    "个人简历",
    "简历",
}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def clean_plain(value: str) -> str:
    text = clean_text(value)
    text = re.sub(r"\s+[.!?]$", "", text)
    replacements = {
        "chatgpt": "ChatGPT",
        "javascript": "JavaScript",
        "powerpoint": "PowerPoint",
        "ppt": "PowerPoint",
    }
    for source, target in replacements.items():
        text = re.sub(rf"\b{re.escape(source)}\b", target, text, flags=re.I)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def clean_bullet(value: str) -> str:
    text = clean_plain(value)
    return re.sub(r"^[^:]{2,40}:\s*", "", text)


def render_rich_text(value: str) -> str:
    escaped = html.escape(value)
    return PLACEHOLDER_RE.sub(
        lambda match: f'<span class="needs-input">[{match.group(1)}]</span>',
        escaped,
    )


def normalize_heading(line: str) -> str:
    text = re.sub(r"[:：]+$", "", line.strip())
    text = re.sub(r"\s+", " ", text)
    return text.upper()


def parse_resume(text: str) -> tuple[list[str], dict[str, list[str]], list[str]]:
    header: list[str] = []
    sections: dict[str, list[str]] = {}
    order: list[str] = []
    current: str | None = None
    expanded_lines: list[str] = []
    for line in text.splitlines():
        expanded_lines.extend(expand_heading_line(line))

    for line in expanded_lines:
        key = normalize_heading(line)
        if key in ALIASES:
            current = ALIASES[key]
            if current not in sections:
                sections[current] = []
                order.append(current)
        elif current is None:
            header.append(line)
        else:
            sections[current].append(line)
    return header, sections, order


def expand_heading_line(line: str) -> list[str]:
    stripped = line.rstrip()
    for key in HEADING_KEYS:
        if stripped.endswith(key):
            if len(stripped) == len(key):
                return [stripped]
            prefix = stripped[: -len(key)].rstrip()
            if prefix:
                return [prefix, key]
    for key in HEADING_KEYS:
        if stripped.startswith(key) and len(stripped) > len(key) and stripped[len(key)].isspace():
            return [key, stripped[len(key) :].strip()]
    return [stripped]


def choose_template(text: str, requested: str = "auto") -> str:
    if requested in TEMPLATES:
        return requested
    lower = text.lower()
    if any(token in lower for token in ["phd", "ph.d", "doctorate", "dissertation"]):
        return "phd"
    return "masters"


def split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    previous_was_bullet = False
    for line in lines:
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            previous_was_bullet = False
            continue
        is_bullet = bool(BULLET_RE.match(line))
        if previous_was_bullet and not is_bullet:
            blocks.append(current)
            current = []
        current.append(line)
        previous_was_bullet = is_bullet
    if current:
        blocks.append(current)
    return blocks


def split_entry_line(line: str) -> tuple[str, str]:
    match = DATE_TAIL_RE.match(line.strip())
    if match and match.group(1).strip() and match.group(2).strip():
        return match.group(1).strip(), match.group(2).strip()
    match = DATE_LEAD_RE.match(line.strip())
    if match and match.group(1).strip() and match.group(2).strip():
        rest = match.group(2).strip()
        if re.match(r"^[-–—]|^(?:present|now)\b", rest, re.I):
            return line.strip(), ""
        return rest, match.group(1).strip()
    return line.strip(), ""


def render_header(header_lines: list[str]) -> str:
    lines = [line.strip() for line in header_lines if line.strip()]
    lines = [
        line
        for line in lines
        if line.lower() not in GENERIC_HEADER_TITLES and "resume sample" not in line.lower()
    ]
    if not lines:
        name = "Your Name"
        contact = ""
    elif len(lines) == 1 and "|" in lines[0]:
        parts = [clean_text(part) for part in lines[0].split("|") if part.strip()]
        name = parts[0] if parts else "Your Name"
        contact = " | ".join(parts[1:])
    elif "@" in lines[0] or re.search(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}", lines[0]):
        name = "Your Name"
        contact = " | ".join(clean_text(line) for line in lines)
    else:
        name = clean_text(lines[0])
        contact = " | ".join(clean_text(line) for line in lines[1:])
    contact = re.sub(r"\s*!\s*", " | ", contact)
    contact_html = f'<div class="contact">{html.escape(contact)}</div>' if contact else ""
    return f'<header><div class="name">{html.escape(name)}</div>{contact_html}</header>'


def render_entry_block(block: list[str]) -> str:
    header_lines = [line for line in block if not BULLET_RE.match(line)]
    bullets = [BULLET_RE.match(line).group(1) for line in block if BULLET_RE.match(line)]
    parts: list[str] = ['<div class="entry">']
    if header_lines:
        first_left, first_right = split_entry_line(header_lines[0])
        parts.append('<div class="entry-head">')
        parts.append(f'<span class="entry-left">{html.escape(first_left)}</span>')
        if first_right:
            parts.append(f'<span class="entry-right">{html.escape(first_right)}</span>')
        parts.append("</div>")
        for line in header_lines[1:]:
            left, right = split_entry_line(line)
            if right:
                parts.append(
                    f'<div class="entry-sub"><span>{html.escape(left)}</span><span>{html.escape(right)}</span></div>'
                )
            else:
                parts.append(f'<div class="entry-sub">{html.escape(left)}</div>')
    if bullets:
        parts.append('<ul class="bullets">')
        for bullet in bullets:
            parts.append(f"<li>{render_rich_text(clean_bullet(bullet))}</li>")
        parts.append("</ul>")
    parts.append("</div>")
    return "".join(parts)


def render_plain_section(lines: list[str], section: str) -> str:
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = BULLET_RE.match(line)
        text = clean_plain(match.group(1) if match else stripped)
        if section == "SKILLS" and ":" in text and not text.lower().startswith("http"):
            category, rest = text.split(":", 1)
            if len(category) <= 40:
                text = f"<strong>{html.escape(category.strip())}:</strong>{render_rich_text(rest)}"
            else:
                text = render_rich_text(text)
        else:
            text = render_rich_text(text)
        items.append(f"<li>{text}</li>")
    if not items:
        return ""
    return '<ul class="plain-list">' + "".join(items) + "</ul>"


def render_section(section: str, lines: list[str], template: str) -> str:
    config = TEMPLATES[template]
    label = config["labels"].get(section, section.replace("_", " ").title())
    if section == "PROFILE":
        text = " ".join(clean_text(line) for line in lines if line.strip())
        body = f'<p class="summary">{render_rich_text(text)}</p>' if text else ""
    elif section in PLAIN_SECTIONS:
        body = render_plain_section(lines, section)
    else:
        body = "".join(render_entry_block(block) for block in split_blocks(lines))
    if not body.strip():
        return ""
    heading_class = "section-title"
    return (
        f'<section class="section section-{section.lower()}">'
        f'<h2 class="{heading_class}">{html.escape(label)}</h2>{body}</section>'
    )


def template_css(template: str) -> str:
    config = TEMPLATES[template]
    heading_case = "uppercase" if config["section_case"] == "uppercase" else "none"
    serif_weight = "600" if config["serif"] else "700"
    return f"""
    :root {{
      --ink: #111;
      --muted: #333;
      --rule: #222;
      --accent: #222;
      --page-width: 8.5in;
      --page-height: 11in;
      --page-padding-y: 0.68in;
      --page-padding-x: 0.75in;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #e7e9ee;
      color: var(--ink);
      font-family: {config['font']};
      font-size: 10.5pt;
      line-height: 1.36;
    }}
    .page {{
      width: var(--page-width);
      min-height: var(--page-height);
      padding: var(--page-padding-y) var(--page-padding-x);
      margin: 24px auto;
      background: #fff;
      box-shadow: 0 10px 35px rgba(15, 23, 42, 0.18);
    }}
    .name {{
      font-size: 21pt;
      font-weight: {serif_weight};
      letter-spacing: 0.2px;
      line-height: 1.1;
    }}
    .contact {{
      margin-top: 4px;
      color: var(--muted);
      font-size: 9.3pt;
      letter-spacing: 0.1px;
    }}
    .section {{ margin-top: 13px; }}
    .section-title {{
      margin: 0 0 5px;
      padding-bottom: 2px;
      border-bottom: 1.25px solid var(--rule);
      color: var(--accent);
      font-size: 10pt;
      font-weight: 700;
      letter-spacing: 0.75px;
      text-transform: {heading_case};
    }}
    .summary {{ margin: 3px 0 0; }}
    .entry {{ margin: 0 0 7px; break-inside: avoid; page-break-inside: avoid; }}
    .entry-head {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 14px;
      font-weight: 600;
    }}
    .entry-left {{ flex: 1 1 auto; }}
    .entry-right {{ flex: 0 0 auto; white-space: nowrap; }}
    .entry-sub {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      color: var(--muted);
      font-size: 9.8pt;
      margin-top: 1px;
    }}
    .bullets {{ margin: 3px 0 0 0; padding-left: 17px; }}
    .bullets li {{ margin: 0 0 2px; padding-left: 1px; }}
    .plain-list {{ margin: 3px 0 0 0; padding-left: 0; list-style: none; }}
    .plain-list li {{ margin: 0 0 2px; }}
    .plain-list strong {{ font-weight: 700; }}
    .needs-input {{
      padding: 0 2px;
      border-bottom: 1px dashed #b45309;
      background: #fff3cd;
      color: #7c2d12;
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      padding: 12px 18px;
      background: rgba(17, 24, 39, 0.96);
      color: #fff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .toolbar span {{ margin-right: auto; font-size: 13px; }}
    .toolbar button, .toolbar a {{
      appearance: none;
      border: 1px solid rgba(255,255,255,0.35);
      background: #fff;
      color: #111;
      border-radius: 6px;
      padding: 7px 12px;
      font-size: 13px;
      text-decoration: none;
      cursor: pointer;
    }}
    .toolbar a {{ background: transparent; color: #fff; }}
    @media screen and (max-width: 900px) {{
      .page {{ width: 100%; min-height: auto; margin: 0; box-shadow: none; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      .toolbar {{ display: none !important; }}
      .page {{ width: auto; min-height: auto; margin: 0; padding: 0; box-shadow: none; }}
      @page {{ size: Letter; margin: 0.6in 0.68in; }}
      .section, .entry {{ break-inside: avoid; page-break-inside: avoid; }}
    }}
    """


def build_resume_html(
    text: str,
    template: str = "auto",
    include_toolbar: bool = False,
    prelude_html: str = "",
    extra_css: str = "",
    download_name: str = "resume-rebuilt.html",
    document_title: str = "Rebuilt Resume",
) -> str:
    template_name = choose_template(text, template)
    config = TEMPLATES[template_name]
    header, sections, original_order = parse_resume(text)

    ordered_sections = [section for section in config["order"] if sections.get(section)]
    ordered_sections += [section for section in original_order if section not in ordered_sections and sections.get(section)]

    body_parts = [render_header(header)]
    for section in ordered_sections:
        rendered = render_section(section, sections[section], template_name)
        if rendered:
            body_parts.append(rendered)

    toolbar = ""
    if include_toolbar:
        toolbar = """
        <div class="toolbar">
          <span>Resume Fixer - rebuilt with the page 34 / 36 / 37 templates</span>
          <button type="button" onclick="window.print()">Print / Save as PDF</button>
          <button type="button" onclick="downloadHtml()">Download HTML</button>
          <a href="/settings">AI settings</a>
          <a href="/">Use another resume</a>
        </div>
        <script>
        function downloadHtml() {
          const clone = document.documentElement.cloneNode(true);
          const bar = clone.querySelector('.toolbar');
          if (bar) bar.remove();
          const blob = new Blob(['<!doctype html>\\n' + clone.outerHTML], {type: 'text/html'});
          const link = document.createElement('a');
          link.href = URL.createObjectURL(blob);
          link.download = __DOWNLOAD_NAME__;
          link.click();
          URL.revokeObjectURL(link.href);
        }
        </script>
        """.replace("__DOWNLOAD_NAME__", json.dumps(download_name))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(document_title)}</title>
  <style>{template_css(template_name)}{extra_css}</style>
</head>
<body>
  {toolbar}
  {prelude_html}
  <main class="page" data-template="{html.escape(template_name)}">
    {''.join(body_parts)}
  </main>
</body>
</html>
"""
