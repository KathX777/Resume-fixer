# Project Notes

## Current status

Version: `0.6.7`

This is a local-first resume tool with a rule-based review, safe formatting
repair, optional BYOK AI rewrite/translation, and HTML rebuild using three
templates modeled on PDF pages 34, 36, and 37. A local browser page supports
paste/upload, provider settings, AI rewrite, review, and one-pass formatting. It
accepts TXT, Markdown, DOCX, and PDF input. AI uses the user's own
OpenAI-compatible provider. DOCX export and native one-click PDF export are not
built yet.

## What works

- Contact-header checks.
- Section detection for education, experience, leadership, projects, and skills.
- Weak-verb and vague-language detection.
- Bullet length checks.
- Result/metric coverage checks.
- Date-format checks.
- Summary/headline checks for advanced-degree resumes.
- Research, teaching, publications, service, awards, and activities detection.
- Publication-year checks for PhD/research resumes.
- Two-page-aware length rules for advanced-degree resumes.
- Scorecard, top-three fixes, section audit, and rewrite worksheet.
- JSON output for future UI integration.
- Rebuild a resume into formatted HTML using `masters`, `phd`, or `technical`
  templates.
- Local browser page with paste/upload, template selection, print-to-PDF, and
  HTML download.
- Combined review-and-rebuild result page with score, top fixes, full findings,
  and a safe-change log.
- Formatting-only normalization for headings, bullets, whitespace, generic
  title lines, and common tool names; no facts or metrics are invented.
- Desktop launcher: `Start Resume Fixer.command`.
- TXT, Markdown, DOCX, and PDF text extraction.
- Common Chinese section-heading aliases and numeric/Chinese-style date ranges.
- Versioned snapshots in `versions/v0.5.0/`, `versions/v0.6.0/`,
  `versions/v0.6.1/`, `versions/v0.6.2/`, `versions/v0.6.3/`, and
  `versions/v0.6.4/`, `versions/v0.6.5/`, `versions/v0.6.6/`, and
  `versions/v0.6.7/`, plus a current release ZIP on the Desktop.
- Automatic port fallback when an older Resume Fixer server still owns 8765.
- Launcher cleanup of older Resume Fixer server processes before starting.
- Visible app version and explicit **AI rewrite ON/OFF** banners.
- Local-only results explicitly say that text was not rewritten.
- `/health` diagnostic endpoint with provider/model readiness and no key data.
- DeepSeek provider preset and `deepseek-chat` model correction.
- Remember-key enabled by default for newly entered keys.
- DeepSeek saves normalize to `https://api.deepseek.com/v1` and show the exact
  effective `/chat/completions` URL.
- Single-instance server lock prevents two sessions with different key state.
- Redacted provider diagnostics in `~/.resume-fixer/diagnostics.log` and the
  local `/diagnostics` page.
- Automatic system CA bundle fallback for python.org macOS builds with an empty
  OpenSSL trust store.
- Optional custom CA PEM path for VPN or corporate proxy interception.
- GitHub-ready README, upload checklist, and `.gitignore`.
- Optional BYOK AI rewrite and Chinese-to-English translation.
- AI settings page with local key storage, session-only key support, and
  connection test.
- Guarded AI prompt and post-response checks for fabricated numbers and lost
  contact details.
- Generic `rules.md` guidance loaded into the AI system prompt before each
  rewrite; the app no longer reads a handbook-derived pattern file.
- Abstract Harvard-inspired formatting rules for section order, typography,
  bullets, accessibility, and layout hygiene.
- Company-specific refinement panel on the result page with a large guidance
  text box, separate AI tailoring request, side-by-side comparison, and
  accept-or-keep controls.
- Removed the `examples/` folder and all example-resume references to avoid
  shipping sample-derived personal or handbook content.
- Original-versus-rewritten scoring, AI rewrite examples, fact prompts, and
  warnings in the result page.
- CLI AI rewrite flags: `--ai-rewrite`, `--target-role`, `--target-language`.
- Beginner AI setup guide: `AI_SETUP.md`.

## Testing notes

- Python compilation, CLI review, all three templates, DOCX extraction, and the
  combined review/rebuild page have been tested directly.
- Binding a local HTTP port is blocked in the current sandbox, so the
  double-click browser workflow should be checked manually on the Mac with
  `Start Resume Fixer.command`.
- The AI client has been tested with mocked provider responses. A live API call
  requires the user's own provider account and was not testable in this
  sandbox.
- The sandbox could not resolve official provider documentation domains, so the
  provider client uses the stable OpenAI-compatible chat-completions shape and
  should be verified against the chosen provider when first connected.
- Port fallback was tested with mocked bind failures because the sandbox blocks
  real local port binding.
- v0.6.2 form, settings, missing-key, invalid-model, and AI-ready states were
  tested directly in Python. The result page was checked for the explicit
  local-formatting-only message.
- v0.6.3 provider normalization, remember-key defaults, diagnostics redaction,
  file permissions, and cross-process single-instance locking were tested.
- v0.6.4 system CA fallback, custom CA loading, TLS-required context creation,
  and request-context integration were tested. A live DeepSeek TLS handshake is
  still blocked from the coding sandbox's network.
- v0.6.5 `rules.md` loading, system-prompt assembly, and the absence of any
  example-folder dependency were tested directly.
- v0.6.6 Harvard-inspired formatting rules were checked for prompt loading,
  section coverage, and the absence of copied names, sample text, or bullets.
- v0.6.7 company-tailoring prompt strings, standalone AI call, result-page
  panel, comparison markup, and accept/keep forms were tested with mocked
  provider responses.

## Next steps

1. Add DOCX export and a one-click native PDF export path.
2. Add provider-specific adapters beyond OpenAI-compatible endpoints.
3. Add saved review history and before/after version comparison.
4. Add OCR for scanned/image-only resumes.
5. Add optional fact-checking against user-provided evidence.

## How to resume work later

Point the assistant to:

`~/resume-fixer`

Then ask it to read `README.md`, `PROJECT_NOTES.md`, and `CHANGELOG.md` first.
Those files describe the current state and next steps. The assistant can then
continue from the existing code rather than starting over.

## Versioning convention

Use `MAJOR.MINOR.PATCH`:

- `MAJOR`: a breaking redesign or a product-level change.
- `MINOR`: a new feature, such as upload support or AI rewriting.
- `PATCH`: a bug fix or small wording/UI change.

Keep the live script named `resume_fixer.py`. Record changes in
`CHANGELOG.md` and update `VERSION`. If you want a snapshot, copy the whole
folder to `versions/v0.1.0/` instead of renaming the live script. This keeps
shortcuts and future imports from breaking.
