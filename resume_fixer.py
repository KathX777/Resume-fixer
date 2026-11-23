#!/usr/bin/env python3
"""Local, rule-based resume feedback tool.

Primed with patterns from the MIT Career Handbook 2019 sample resumes
(PDF pages 27-40). No external dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUBRIC = json.loads((ROOT / "rubric.json").read_text(encoding="utf-8"))
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DIMENSIONS: dict[str, dict[str, Any]] = RUBRIC["dimensions"]
ALIASES = {key.upper(): value for key, value in RUBRIC["section_aliases"].items()}
RESULT_SECTIONS = set(RUBRIC["result_sections"])
WEAK_STARTS = {verb.lower() for verb in RUBRIC["weak_starts"]}
VAGUE_PHRASES = [phrase.lower() for phrase in RUBRIC["vague_phrases"]]
RESULT_WORDS = [word.lower() for word in RUBRIC["result_words"]]
IDEAL_WORDS = tuple(RUBRIC["rules"]["ideal_word_range"])
ADVANCED_WORDS = tuple(RUBRIC["rules"]["advanced_word_range"])
ADVANCED_MIN_WORDS = int(RUBRIC["rules"]["advanced_min_words"])
MAX_BULLET_CHARS = int(RUBRIC["rules"]["max_bullet_chars"])
MIN_EXPERIENCE_BULLETS = int(RUBRIC["rules"]["min_experience_bullets"])
TARGET_METRIC_COVERAGE = float(RUBRIC["rules"]["target_metric_coverage"])
MAX_SUMMARY_WORDS = int(RUBRIC["rules"]["max_summary_words"])
ADVANCED_RE = re.compile(
    "|".join(re.escape(pattern) for pattern in RUBRIC["advanced_profile_patterns"]),
    re.I,
)
RESEARCH_RE = re.compile(
    "|".join(re.escape(pattern) for pattern in RUBRIC["research_profile_patterns"]),
    re.I,
)

BULLET_RE = re.compile(r"^\s*(?:[•●▪◦*\-–—]|\d+[.)])\s+(.*\S)\s*$")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")
URL_RE = re.compile(r"(?:https?://|www\.|linkedin\.com|github\.com|behance\.net|\.me\b)", re.I)
METRIC_RE = re.compile(
    r"(?:\$\s?\d[\d,.]*|€\s?\d[\d,.]*|£\s?\d[\d,.]*|"
    r"\b\d+(?:[.,]\d+)?\s?%|"
    r"\b\d+(?:[.,]\d+)?\s?(?:k|m|bn|x)\b|"
    r"\b\d{2,}\b)",
    re.I,
)
DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|"
    r"\b(?:19|20)\d{2}\s*[-–—]\s*(?:(?:19|20)\d{2}|Present)\b|"
    r"\b(?:19|20)\d{2}[./-]\d{1,2}\b",
    re.I,
)
NUMERIC_DATE_RE = re.compile(r"\b(?:19|20)\d{2}[./-]\d{1,2}\b")
MONTH_DATE_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",
    re.I,
)
PRONOUN_RE = re.compile(r"\b(?:I|me|my|mine)\b")


def short(text: str, limit: int = 140) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def normalize_heading(line: str) -> str:
    text = re.sub(r"[:：]+$", "", line.strip())
    text = re.sub(r"\s+", " ", text)
    return text.upper()


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"HEADER": []}
    current = "HEADER"
    for line in text.splitlines():
        key = normalize_heading(line)
        if key in ALIASES:
            current = ALIASES[key]
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def parse_bullets(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        match = BULLET_RE.match(line)
        if match:
            bullets.append(match.group(1).strip())
    return bullets


def first_word(text: str) -> str:
    match = re.match(r"[A-Za-z][A-Za-z'’-]*", text.strip())
    return match.group(0).lower() if match else ""


def has_metric(text: str) -> bool:
    for match in METRIC_RE.finditer(text):
        token = match.group(0).strip()
        if re.fullmatch(r"(?:19|20)\d{2}", token):
            continue
        return True
    return False


def has_result(text: str) -> bool:
    lower = text.lower()
    return has_metric(text) or any(word in lower for word in RESULT_WORDS)


def bullet_flags(bullet: str) -> list[str]:
    flags: list[str] = []
    if first_word(bullet) in WEAK_STARTS:
        flags.append("weak opening verb")
    if not has_result(bullet):
        flags.append("no measurable result")
    if any(phrase in bullet.lower() for phrase in VAGUE_PHRASES):
        flags.append("vague language")
    if len(bullet) > MAX_BULLET_CHARS:
        flags.append("too long")
    if PRONOUN_RE.search(bullet):
        flags.append("first-person pronoun")
    return flags


def add_issue(
    issues: list[dict[str, Any]],
    category: str,
    severity: str,
    message: str,
    evidence: str = "",
    fix: str = "",
    deduction: int = 0,
) -> None:
    issues.append(
        {
            "category": category,
            "severity": severity,
            "message": message,
            "evidence": evidence,
            "fix": fix,
            "deduction": deduction,
        }
    )


def audit(text: str, sections: dict[str, list[str]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    advanced = bool(ADVANCED_RE.search(text))
    research_profile = bool(RESEARCH_RE.search(text))

    missing_contact: list[str] = []
    if not EMAIL_RE.search(text):
        missing_contact.append("email")
    if not PHONE_RE.search(text):
        missing_contact.append("phone")
    if not URL_RE.search(text):
        missing_contact.append("LinkedIn/portfolio link")
    if missing_contact:
        add_issue(
            issues,
            "contact",
            "high",
            "Missing contact details: " + ", ".join(missing_contact),
            fix="Add a one-line header: name | email | phone | LinkedIn/portfolio | city.",
            deduction=10,
        )

    required_sections = ["EDUCATION", "EXPERIENCE", "SKILLS"]
    missing_sections = [section for section in required_sections if not any(sections.get(section, []))]
    if "EXPERIENCE" in missing_sections and any(
        sections.get(section) for section in ["LEADERSHIP", "RESEARCH", "TEACHING", "PROJECTS"]
    ):
        missing_sections.remove("EXPERIENCE")
    if missing_sections:
        add_issue(
            issues,
            "structure",
            "high",
            "Missing or unreadable sections: " + ", ".join(missing_sections),
            fix="Use standard headings: EDUCATION, EXPERIENCE, PROJECTS, SKILLS.",
            deduction=min(12, 4 * len(missing_sections)),
        )

    profile_lines = [line for line in sections.get("PROFILE", []) if line.strip()]
    if profile_lines:
        profile_text = " ".join(profile_lines).strip()
        profile_words = len(re.findall(r"\b[\w'’-]+\b", profile_text))
        if profile_words > MAX_SUMMARY_WORDS:
            add_issue(
                issues,
                "language",
                "medium",
                f"Summary is too long ({profile_words} words).",
                fix="Trim it to 2-4 lines: role/domain, strongest evidence, and target.",
                deduction=3,
            )
        if not re.search(
            r"\b(?:seeking|targeting|interested in|focus(?:ed)? on|experience in|professional|track record)\b",
            profile_text,
            re.I,
        ):
            add_issue(
                issues,
                "structure",
                "low",
                "Summary does not state a target role or professional focus.",
                fix="Add a role or domain focus, then one or two proof points.",
                deduction=2,
            )
    elif advanced:
        add_issue(
            issues,
            "structure",
            "medium",
            "No summary or target-role headline found for an advanced-degree resume.",
            fix="Add a 2-3 line SUMMARY or a headline such as 'PhD in Materials Science | Interested in Consulting'.",
            deduction=3,
        )

    publication_lines = [line for line in sections.get("PUBLICATIONS", []) if line.strip()]
    if research_profile:
        if not publication_lines:
            add_issue(
                issues,
                "impact",
                "medium",
                "No publications section found for a PhD/research resume.",
                fix="Add a PUBLICATIONS section with author order, title, venue, year, and any under-review work.",
                deduction=4,
            )
        elif not re.search(r"\b(?:19|20)\d{2}\b", " ".join(publication_lines)):
            add_issue(
                issues,
                "impact",
                "low",
                "Publications do not include years.",
                fix="Add year, venue, and author order so reviewers can judge recency and contribution.",
                deduction=2,
            )

    all_bullets: list[str] = []
    for lines in sections.values():
        all_bullets.extend(parse_bullets(lines))

    result_bullets: list[str] = []
    for section in RESULT_SECTIONS:
        result_bullets.extend(parse_bullets(sections.get(section, [])))

    if len(all_bullets) < 5:
        add_issue(
            issues,
            "structure",
            "medium",
            f"Only {len(all_bullets)} bullet points found.",
            fix="Use bullets instead of paragraphs; aim for 2-4 per experience.",
            deduction=5,
        )

    if result_bullets:
        result_count = sum(1 for bullet in result_bullets if has_result(bullet))
        coverage = result_count / len(result_bullets)
        if coverage < TARGET_METRIC_COVERAGE:
            deduction = 15 if coverage < 0.35 else 8
            add_issue(
                issues,
                "par",
                "high",
                f"Only {result_count}/{len(result_bullets)} experience/project bullets include a result or metric.",
                fix="Add scale or outcome: people, %, $, time saved, rank, conversion, or what changed.",
                deduction=deduction,
            )
        for section in RESULT_SECTIONS:
            section_bullets = parse_bullets(sections.get(section, []))
            if section_bullets and len(section_bullets) < MIN_EXPERIENCE_BULLETS:
                add_issue(
                    issues,
                    "structure",
                    "medium",
                    f"{section} has only {len(section_bullets)} bullet(s).",
                    fix="Add another bullet covering a distinct action and result.",
                    deduction=3,
                )
    else:
        add_issue(
            issues,
            "par",
            "high",
            "No experience, research, teaching, leadership, or project bullets found.",
            fix="Add 2-4 bullets per experience using: context + action + result.",
            deduction=20,
        )

    weak = [bullet for bullet in all_bullets if first_word(bullet) in WEAK_STARTS]
    if weak:
        add_issue(
            issues,
            "language",
            "medium",
            f"{len(weak)} bullet(s) start with weak verbs.",
            evidence=" | ".join(short(bullet) for bullet in weak[:3]),
            fix="Start with a specific action verb: Led, Built, Analyzed, Coordinated, Reduced, etc.",
            deduction=min(12, 2 * len(weak)),
        )

    vague = [
        (bullet, [phrase for phrase in VAGUE_PHRASES if phrase in bullet.lower()])
        for bullet in all_bullets
    ]
    vague = [(bullet, hits) for bullet, hits in vague if hits]
    if vague:
        add_issue(
            issues,
            "impact",
            "medium",
            f"{len(vague)} bullet(s) contain vague or low-evidence language.",
            evidence=" | ".join(short(bullet) for bullet, _ in vague[:3]),
            fix="Replace vague phrases with a specific action and result.",
            deduction=min(10, 2 * len(vague)),
        )

    long_bullets = [bullet for bullet in all_bullets if len(bullet) > MAX_BULLET_CHARS]
    if long_bullets:
        add_issue(
            issues,
            "format",
            "medium",
            f"{len(long_bullets)} bullet(s) are too long.",
            evidence=" | ".join(short(bullet) for bullet in long_bullets[:3]),
            fix="Split into two bullets or cut to one line: action + result.",
            deduction=min(6, 2 * len(long_bullets)),
        )

    pronoun_bullets = [bullet for bullet in all_bullets if PRONOUN_RE.search(bullet)]
    if pronoun_bullets:
        add_issue(
            issues,
            "language",
            "low",
            f"{len(pronoun_bullets)} bullet(s) use first-person pronouns.",
            evidence=" | ".join(short(bullet) for bullet in pronoun_bullets[:3]),
            fix="Remove I/me/my; start with the action verb.",
            deduction=min(5, len(pronoun_bullets)),
        )

    word_count = len(re.findall(r"\b[\w'’-]+\b", text))
    word_range = ADVANCED_WORDS if advanced else IDEAL_WORDS
    minimum_words = ADVANCED_MIN_WORDS if advanced else 150
    if word_count > word_range[1]:
        add_issue(
            issues,
            "format",
            "medium",
            f"Resume is long ({word_count} words; target {word_range[0]}-{word_range[1]}).",
            fix=(
                "Advanced resumes may use two pages; cut repetition and keep the strongest evidence."
                if advanced
                else "Cut repetition and keep one page for early-career roles."
            ),
            deduction=4,
        )
    elif word_count < minimum_words:
        add_issue(
            issues,
            "format",
            "medium",
            f"Resume is short ({word_count} words).",
            fix="Add scope, actions, and results to experience, research, teaching, and projects.",
            deduction=6 if advanced else 4,
        )

    experience_text = "\n".join(
        sections.get("EXPERIENCE", [])
        + sections.get("LEADERSHIP", [])
        + sections.get("RESEARCH", [])
        + sections.get("TEACHING", [])
        + sections.get("PROJECTS", [])
        + sections.get("SERVICE", [])
    )
    if experience_text.strip() and not DATE_RE.search(experience_text):
        add_issue(
            issues,
            "format",
            "medium",
            "No dates detected in the experience sections.",
            fix="Add dates in a consistent format, such as Feb 2024 - Jun 2026.",
            deduction=3,
        )
    if NUMERIC_DATE_RE.search(text) and MONTH_DATE_RE.search(text):
        add_issue(
            issues,
            "format",
            "low",
            "Mixed date formats detected.",
            fix="Pick one format and use it everywhere.",
            deduction=2,
        )

    skills_lines = [line for line in sections.get("SKILLS", []) if line.strip()]
    max_skills_lines = 12 if advanced else 8
    if len(skills_lines) > max_skills_lines:
        add_issue(
            issues,
            "structure",
            "medium",
            f"Skills section is long ({len(skills_lines)} lines).",
            fix="Compress to 3-6 keyword lines, grouped by category.",
            deduction=3,
        )

    return issues


def calculate_scores(issues: list[dict[str, Any]]) -> tuple[dict[str, int], int]:
    deductions = {category: 0 for category in DIMENSIONS}
    for issue in issues:
        category = issue["category"]
        if category in deductions:
            deductions[category] += int(issue.get("deduction", 0))

    scores: dict[str, int] = {}
    for category, meta in DIMENSIONS.items():
        scores[category] = max(0, int(meta["max"]) - deductions[category])
    return scores, sum(scores.values())


def readiness(total: int, issues: list[dict[str, Any]]) -> str:
    if any(issue["category"] == "contact" for issue in issues):
        return "Critical - add contact details before anything else"
    if total >= 90:
        return "Strong - ready for a final proofread"
    if total >= 75:
        return "Good base - tighten results and consistency"
    if total >= 50:
        return "Needs work - fix structure and evidence"
    return "Major revision - rebuild the core sections"


def top_fixes(issues: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    category_rank = {
        "contact": 0,
        "structure": 1,
        "par": 2,
        "impact": 3,
        "language": 4,
        "format": 5,
    }
    ordered = sorted(
        issues,
        key=lambda issue: (
            severity_rank.get(issue["severity"], 3),
            category_rank.get(issue["category"], 9),
            -int(issue.get("deduction", 0)),
        ),
    )
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for issue in ordered:
        if issue["message"] in seen:
            continue
        seen.add(issue["message"])
        result.append(issue)
        if len(result) == limit:
            break
    return result


def print_report(
    sections: dict[str, list[str]],
    issues: list[dict[str, Any]],
    scores: dict[str, int],
    total: int,
    advanced: bool,
) -> None:
    print(f"\nRESUME FIXER v{VERSION}")
    print(f"Profile detected: {'Advanced degree / research' if advanced else 'Early career'}")
    print(f"Readiness: {total}/100 - {readiness(total, issues)}")

    print("\nTOP 3 FIXES")
    for index, issue in enumerate(top_fixes(issues), 1):
        print(f"{index}. {issue['message']}")
        if issue["evidence"]:
            print(f"   Evidence: {issue['evidence']}")
        if issue["fix"]:
            print(f"   Fix: {issue['fix']}")

    print("\nSCORECARD")
    for category, meta in DIMENSIONS.items():
        print(f"- {meta['label']}: {scores[category]}/{meta['max']}")

    print("\nSECTION AUDIT")
    for section in [
        "PROFILE",
        "EDUCATION",
        "EXPERIENCE",
        "LEADERSHIP",
        "RESEARCH",
        "TEACHING",
        "PROJECTS",
        "PUBLICATIONS",
        "SERVICE",
        "AWARDS",
        "SKILLS",
        "ACTIVITIES",
        "INTERESTS",
    ]:
        if section in sections:
            lines = [line for line in sections[section] if line.strip()]
            bullets = parse_bullets(sections[section])
            label = "SUMMARY" if section == "PROFILE" else section
            print(f"- {label}: {len(lines)} line(s), {len(bullets)} bullet(s)")

    print("\nBULLET REWRITE WORKSHEET")
    flagged: list[tuple[str, str, list[str]]] = []
    for section in ["EXPERIENCE", "LEADERSHIP", "RESEARCH", "TEACHING", "PROJECTS", "SERVICE"]:
        for bullet in parse_bullets(sections.get(section, [])):
            flags = bullet_flags(bullet)
            if flags:
                flagged.append((section, bullet, flags))

    if not flagged:
        print("No bullet-level issues detected in experience, research, teaching, leadership, projects, or service.")
    else:
        for index, (section, bullet, flags) in enumerate(flagged[:8], 1):
            print(f"{index}. [{section}] {short(bullet, 170)}")
            print(f"   Problems: {', '.join(flags)}")
            print("   Rewrite: [strong verb] + [what you did] + [scale/result].")

    print("\nQUESTIONS TO ANSWER BEFORE REWRITING")
    for question in [
        "What was the scale? (people, events, budget, team size)",
        "What changed because of your work? (%, $, time, rank, conversion)",
        "What was your specific action, rather than the team's?",
        "What tools or methods did you use?",
        "For research: what question, method, and result did you contribute?",
        "For teaching: how many students, what did you teach, and what changed?",
        "For publications: author order, venue, year, and under-review status?",
    ]:
        print(f"- {question}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rule-based resume feedback.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("file", nargs="?", help="Path to a plain-text resume")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--rebuild",
        metavar="INPUT",
        help="Create a formatted HTML resume from a plain-text resume",
    )
    parser.add_argument(
        "--output",
        metavar="OUTPUT",
        help="Output path for --rebuild (default: INPUT-rebuilt.html)",
    )
    parser.add_argument(
        "--template",
        choices=["auto", "masters", "phd", "technical"],
        default="auto",
        help="Formatting standard: masters (p34), phd (p36), technical (p37), or auto",
    )
    parser.add_argument(
        "--ai-rewrite",
        action="store_true",
        help="Use the configured BYOK AI provider to rewrite/translate before rebuilding",
    )
    parser.add_argument(
        "--target-role",
        default="",
        help="Optional target role for --ai-rewrite",
    )
    parser.add_argument(
        "--target-language",
        default="English",
        help="Target language for --ai-rewrite (default: English)",
    )
    parser.add_argument("--serve", action="store_true", help="Start the local upload/rebuild web page")
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Starting port for --serve; the next free port is used if busy",
    )
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser when using --serve")
    args = parser.parse_args()

    if args.ai_rewrite and not args.rebuild:
        parser.error("--ai-rewrite requires --rebuild INPUT")

    if args.serve:
        from resume_web import serve

        serve(args.port, open_browser=not args.no_browser)
        return

    if args.rebuild:
        from resume_formatter import build_resume_html
        from resume_io import extract_resume_text
        from resume_repair import repair_resume

        source = Path(args.rebuild)
        text = extract_resume_text(source)
        if args.ai_rewrite:
            from resume_ai import AIClientError, rewrite_resume_with_ai
            from resume_settings import load_settings

            try:
                report = rewrite_resume_with_ai(
                    text,
                    load_settings(),
                    target_role=args.target_role,
                    target_language=args.target_language,
                )
            except AIClientError as exc:
                parser.error(str(exc))
            print(f"AI rewrite: {report.provider} ({report.model})")
            text = report.resume_text
        text, _ = repair_resume(text)
        output = (
            Path(args.output)
            if args.output
            else source.with_name(f"{source.stem}-rebuilt.html")
        )
        output.write_text(build_resume_html(text, template=args.template), encoding="utf-8")
        print(f"Wrote formatted resume: {output}")
        return

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    if not text.strip():
        parser.error("No resume text provided.")

    sections = parse_sections(text)
    issues = audit(text, sections)
    scores, total = calculate_scores(issues)
    advanced = bool(ADVANCED_RE.search(text))

    if args.json:
        print(
            json.dumps(
                {
                    "version": VERSION,
                    "profile": "advanced" if advanced else "early",
                    "total": total,
                    "readiness": readiness(total, issues),
                    "scores": scores,
                    "issues": issues,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print_report(sections, issues, scores, total, advanced)


if __name__ == "__main__":
    main()
