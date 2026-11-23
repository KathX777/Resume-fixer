# Changelog

All notable changes to Resume Fixer should be recorded here.

## [0.6.7] - 2026-11-23

### Added

- Added a **Tailor to a specific company** panel to the result page with a
  large company-guideline and job-description input.
- Added a separate company-tailoring AI call using the current revised resume
  and a dedicated system prompt focused on keywords, tone, and emphasis.
- Added a side-by-side comparison of the current resume and tailored draft.
- Added **Use tailored version** and **Keep current version** controls.

### Changed

- The result page now reports whether AI is ready for company refinement and
  preserves the pasted guidance when a request fails.

## [0.6.6] - 2026-11-23

### Added

- Added a Harvard-inspired formatting section to `rules.md`, covering section
  order, entry structure, font and margin guidance, line spacing, bullet
  structure, accessibility, and common layout mistakes to avoid.

### Privacy

- The new section contains only abstract formatting principles. No sample
  names, school-specific content, or example bullets were copied.

## [0.6.5] - 2026-11-23

### Added

- Added `rules.md`, a generic rulebook with Structure, Tone & Style, Action
  Verbs, and Formatting sections derived from resume-writing principles.
- The AI system prompt now loads `rules.md` and places those rules before the
  application instructions on every rewrite request.

### Changed

- Removed the `examples/` folder, rebuilt example files, and the duplicate
  `knowledge/handbook_patterns.md` prompt file.
- Updated documentation and upload instructions so the project no longer
  references sample resumes.

### Privacy

- No resume samples, personal identities, schools, employers, or contact data
  are included in the shipped rules or documentation.

## [0.6.4] - 2026-11-15

### Fixed

- Solved `SSL: CERTIFICATE_VERIFY_FAILED` on python.org macOS Python builds
  that trust zero CA certificates. The HTTP client now loads the system CA
  bundle automatically when Python's default trust store is empty.
- The launcher exports `SSL_CERT_FILE=/etc/ssl/cert.pem` when no certificate
  file is already configured. TLS certificate verification remains enabled.
- Added optional custom CA import and path fields in AI settings for VPN,
  corporate proxy, or antivirus interception certificates. PEM and DER formats
  are supported.
- Certificate failures now explain the likely proxy/certificate cause and
  point to the custom CA setting instead of showing a raw OpenSSL message.

### Added

- The sanitized diagnostics log records the number of trusted CA certificates
  and which local bundle was loaded, never the certificate contents or key.

## [0.6.3] - 2026-11-15

### Fixed

- API keys are now remembered by default when a new key is entered. The setting
  can still be unchecked for session-only use.
- The DeepSeek preset now normalizes saves to
  `https://api.deepseek.com/v1` instead of leaving ambiguous root URLs.
- Resume Fixer now enforces a single running server process. A second launch
  reports the existing version and URL instead of opening another server on a
  fallback port where the session-only API key is missing.
- The settings page shows the exact effective request URL, such as
  `https://api.deepseek.com/v1/chat/completions`.
- Provider HTTP and network errors are written to a local, redacted diagnostics
  log for troubleshooting without storing the resume or exposing the API key.

### Added

- `/diagnostics` page showing recent sanitized connection errors.
- Connection diagnostics also report the exact URL, model, HTTP status, and
  whether a key was present.

## [0.6.2] - 2026-11-15

### Fixed

- The upload page no longer says “rewrite” when AI is unavailable. Its button
  now reads **Review & format locally**, and a prominent banner states that the
  text will not be rewritten or translated.
- Local-only results now say **Local formatting complete — text was not
  rewritten** instead of implying that a rewrite occurred.
- The home page shows the running app version, so an old browser tab is easier
  to spot.
- The launcher stops older Resume Fixer server processes on ports 8765-8774
  before starting the current version.
- DeepSeek setup is easier: the settings page has provider presets, recommends
  the real model ID `deepseek-chat`, and repairs the common mistaken value
  `Deepseek` when settings are saved.
- The settings page warns when no API key is loaded and explains that a
  session-only key disappears when the app restarts.

### Added

- `/health` local JSON endpoint with version, provider, model, port, and AI
  readiness. It never includes the API key.
- Startup output in the Terminal now reports the version and whether AI rewrite
  is ready or off.

## [0.6.1] - 2026-11-15

### Fixed

- The launcher no longer crashes with `OSError: [Errno 48] Address already in
  use` when an older Resume Fixer window still owns port 8765.
- The local server now tries ports 8765-8774, opens the browser on the selected
  free port, and prints a useful message if every port is occupied.

## [0.6.0] - 2026-11-15

### Added

- Optional BYOK AI rewrite mode using an OpenAI-compatible chat-completions
  API, with no bundled key or shared developer account.
- AI settings page for base URL, model, API key, target language, connection
  testing, and remembering or forgetting the key locally.
- Guarded rewrite prompt covering translation, PAR structure, strong verbs,
  missing-fact placeholders, and strict no-fabrication rules.
- AI response validation for invalid JSON, missing resume text, new numeric
  values, lost contact details, and large length changes.
- Result page with original and rewritten scores, AI rewrite examples,
  remaining findings, fact-confirmation questions, and warnings.
- Highlighted `[[ADD: ...]]` and `[[CHECK: ...]]` prompts inside the formatted
  resume.
- CLI `--ai-rewrite`, `--target-role`, and `--target-language` options.
- `AI_SETUP.md` for beginner setup and troubleshooting.
- Date-prefix entry support for resumes such as `2026.02 Role Title`.

### Changed

- Version updated to `0.6.0`.
- Privacy documentation now distinguishes local mode from opt-in AI mode.
- GitHub upload instructions now cover API-key handling and the new files.

## [0.5.0] - 2026-11-15

### Added

- Combined upload -> review -> safe repair -> formatted resume workflow on the
  local browser page.
- Review summary above the rebuilt resume with score, readiness, top three
  fixes, full findings, and scorecard.
- `resume_repair.py` for formatting-only normalization with a transparent
  change log. It never changes dates, claims, metrics, or experience.
- Standardized tool-name capitalization (`ChatGPT`, `JavaScript`, `PowerPoint`)
  during safe repair.
- Common Chinese section headings such as `教育背景`, `工作经历`, `项目经历`,
  and `个人技能` are now recognized and converted to standard template headings.
- Date-range rendering now supports numeric and Chinese-style dates such as
  `2023.09 - 2025.06` and `2023年9月 - 2025年6月`.
- Versioned release snapshot in `versions/v0.5.0/` and a downloadable ZIP.
- GitHub-ready `README.md`, beginner upload guide, and `.gitignore`.

### Changed

- The upload page now submits to `/fix` and returns both the review and the
  corrected resume in one result page.
- HTML download filenames now reflect the selected formatting template.

## [0.4.0] - 2026-11-15

### Added

- `resume_io.py` for extracting resume text from `.txt`, `.md`, `.docx`, and
  `.pdf` files.
- DOCX extraction preserves Word bullet characters and repairs split month
  and year lines.
- PDF extraction uses macOS PDFKit and removes page-number/footer noise.
- The upload page now accepts DOCX and PDF files, sends them to the local
  server, and extracts text before rebuilding.
- The `--rebuild` command now accepts DOCX and PDF input directly.

## [0.3.0] - 2026-11-15

### Added

- `resume_formatter.py` for rebuilding a resume into a clean, printable HTML
  document.
- Three formatting standards modeled on PDF pages 34, 36, and 37:
  `masters`, `phd`, and `technical`.
- `--rebuild` command for creating a formatted resume from a plain-text file.
- `--serve` command for a local browser page with paste/upload and template
  selection.
- `resume_web.py` for the local upload/rebuild interface.
- `knowledge/formatting_templates.md` documenting the three layouts.

### Notes

- The rebuild preserves the user's facts; it does not invent metrics or
  experience.
- Output is HTML and prints cleanly to PDF from a browser.

## [0.2.0] - 2026-11-15

### Added

- Advanced-degree and research-resume support derived from MIT Career Handbook
  sample resumes on PDF pages 34-40.
- Recognition for Research, Teaching, Publications, Service, Awards, and
  Activities sections.
- Summary/headline checks for advanced and experienced candidates.
- Publication-year checks for PhD/research resumes.
- Two-page-aware word-count rules for advanced-degree resumes.
- Advanced synthetic demo resume.

### Fixed

- Corrected the scoring weights so the six dimensions total exactly 100 points.
- Corrected the hard-coded version label in the report output.

## [0.1.0] - 2026-11-12

### Added

- Initial rule-based resume feedback prototype.
- Six-dimension scoring rubric: contact, structure, PAR/results, evidence,
  language, and format.
- Checks for contact details, weak verbs, vague phrases, bullet length,
  result coverage, dates, and section presence.
- Sample-derived pattern notes from MIT Career Handbook 2019, PDF pages 27-34.
- Synthetic demo resume with deliberate issues.
