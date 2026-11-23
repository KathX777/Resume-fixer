# Resume Fixer v0.5.0

Released 2026-11-15.

## Main change

The upload page now performs the full workflow in one pass:

1. Load a `.txt`, `.md`, `.docx`, or `.pdf` resume.
2. Review the original resume score, top fixes, and detailed findings.
3. Apply safe formatting-only repairs.
4. Render a corrected resume using the page 34, 36, or 37 formatting standard.
5. Print/save as PDF or download the HTML result.

## Safety rule

The repair step never adds metrics, experience, dates, achievements, or claims.
It only standardizes presentation details and reports every safe change in the
result page.

The parser also recognizes common Chinese section headings and numeric or
Chinese-style date ranges, so a Chinese-language resume can be put into the
English heading layout. Translation of resume content is not included yet.

## Files

- Live application: `resume_fixer.py`
- Complete release snapshot: `versions/v0.5.0/`
- Release archive: `~/Desktop/resume-fixer-v0.5.0.zip`

## Formatting standards

- `masters`: page 34, standard/master's layout.
- `phd`: page 36, formal research layout.
- `technical`: page 37, technical resume with summary and skills near the top.
