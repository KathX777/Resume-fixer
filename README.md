# Resume Fixer

A local-first resume review, AI rewrite, and formatting tool. Upload a resume,
get a rule-based scorecard and handbook-inspired rewrite guidance, optionally
rewrite or translate it with your own AI API, then create a clean resume in one
of three page-based layouts.

**Current version:** `0.6.7`

> AI rewrite is optional and uses the user's own API key. No shared key,
> central resume server, or analytics service is included in this project.

## What it does

- Reviews a resume with a 100-point scorecard covering contact details,
  structure, PAR/results, evidence, language, and ATS-friendly formatting.
- Detects weak verbs, vague language, missing metrics, long bullets, date
  inconsistencies, weak section structure, and advanced-degree requirements.
- Optionally sends the resume to a user-configured AI provider for a complete
  rewrite and Chinese-to-English translation.
- Tailors the current revised resume to pasted company values, recruiter
  guidance, or a job description in a separate AI pass, with side-by-side
  comparison and accept-or-keep controls.
- Rebuilds the result in a clean, printable layout inspired by handbook pages
  34, 36, and 37.
- Shows original versus rewritten scores, AI change examples, missing-fact
  prompts, and safety warnings.
- Highlights unresolved facts as `[[ADD: ...]]` or `[[CHECK: ...]]` instead of
  inventing information.
- Reads `.txt`, `.md`, `.docx`, and `.pdf` files.
- Recognizes common English and Chinese section headings, numeric dates, and
  Chinese-style date ranges.
- Prints to PDF from the browser or downloads an HTML version.

## Two modes

| Mode | What happens | Network required |
| --- | --- | --- |
| Local review and format | Rule-based review, safe formatting repairs, and template rebuild | No |
| AI rewrite and format | A BYOK provider rewrites/translates the resume, then the app reviews and formats it; company-specific refinement can be run afterward | Yes |

The local mode does not rewrite meaning. The AI mode is what performs semantic
rewriting and translation. Every AI-generated draft must still be reviewed by
the user.

## Why this exists

Recruiters scan resumes quickly. A clear structure, visible evidence, and
consistent formatting matter before a reader gets to the content. Resume Fixer
uses these principles from the MIT Career Handbook 2019 resume section:

- Put the most relevant information where a reader can find it immediately.
- Use standard section headings and a consistent visual hierarchy.
- Describe experience with **PAR**: Project/context, Activity, Result.
- Prefer specific evidence over vague claims such as "team player".
- Keep dates, bullets, spacing, and capitalization consistent.
- Use generic structure, tone, action-verb, and formatting rules from the local
  `rules.md` file without relying on sample resumes.

The project is independent and is not affiliated with MIT. It does not include
the handbook or its sample resumes. The templates are structural and
typographic interpretations of the layouts on handbook pages 34, 36, and 37.

## Quick start (macOS)

1. Double-click `Start Resume Fixer.command`.
2. Your browser opens `http://127.0.0.1:8765`.
3. Open **AI settings** and follow [AI_SETUP.md](AI_SETUP.md), or leave AI off
   for local-only review and formatting.
4. Upload a resume or paste its text.
5. Select a formatting standard.
6. Optionally enable **AI rewrite**, choose a target language, enter a target
   role, and paste a job description.
7. Check the status banner. When AI is ready, the button says **Review,
   rewrite & format with AI**. Without a working provider and key, it says
   **Review & format locally** and the app does not claim to rewrite anything.
8. Resolve highlighted missing-fact prompts, then use **Print / Save as PDF**
   or **Download HTML**.

If the launcher does not open:

```bash
cd ~/resume-fixer
python3 resume_fixer.py --serve
```

Then open <http://127.0.0.1:8765>.

The launcher stops older Resume Fixer servers on ports 8765-8774 before starting
the current version. If another application owns those ports, the server selects
the next free port and opens that address instead.

## Bring your own API key

Resume Fixer does not include an API key, proxy, or hosted AI account. Each
user connects their own OpenAI-compatible provider through the **AI settings**
page.

Settings include:

- API base URL.
- Model name.
- API key.
- Default target language.

The default settings are starting points, not a guarantee that a provider or
model name is available on every account. Use the base URL and model name shown
by your provider.

The key is stored only on the user's computer:

- If **Remember the key on this Mac** is checked, it is kept in
  `~/.resume-fixer/credentials.json` with user-only file permissions.
- If unchecked, the key stays in memory until the app stops.
- It is never written to the repository or displayed again in the browser.

See [AI_SETUP.md](AI_SETUP.md) for the full setup and troubleshooting guide.

## AI provider compatibility

The client currently uses the widely supported OpenAI-compatible
`/chat/completions` request format. It can be used with providers that expose a
compatible endpoint, including some hosted and local model servers.

Provider-specific requirements vary. If a provider uses a different API shape,
an adapter will be needed. The app reports HTTP and model errors in the browser
instead of silently switching providers.

## Safety model

The AI prompt requires the model to:

- Preserve names, dates, employers, education, titles, tools, awards, and
  publications.
- Never invent metrics or outcomes.
- Insert `[[ADD: ...]]` when a real result is missing.
- Insert `[[CHECK: ...]]` when translation is ambiguous.
- Use specific action verbs and the PAR pattern.
- Tailor a completed draft to company guidance without changing its overall
  format.
- Return a complete plain-text resume plus a change list and questions.

After the response, Resume Fixer also checks for:

- New numeric values that were not in the original resume.
- Missing email, phone, or profile URL values.
- Large unexplained changes in resume length.

These checks are warnings, not proof of correctness. Verify every claim before
sending a resume to an employer.

## Privacy

Local mode:

- Resume files are processed on the computer.
- Uploaded files are written to a temporary file only long enough to extract
  text, then deleted.
- No resume text is sent over the network.

AI mode:

- Resume text is sent directly from the user's computer to the provider they
  configured.
- Company-specific refinement sends the current revised resume plus the pasted
  company guidance to that provider in a separate request.
- It is not sent through a Resume Fixer developer server.
- The provider's privacy, retention, and billing terms apply.
- Do not enable AI mode for sensitive documents unless the provider is trusted
  for that data.

## Command line

Review:

```bash
cd ~/resume-fixer
python3 resume_fixer.py /path/to/your-resume.txt
```

Review as JSON:

```bash
python3 resume_fixer.py /path/to/your-resume.txt --json
```

Local format rebuild:

```bash
python3 resume_fixer.py --rebuild /path/to/your-resume.txt \
  --template phd \
  --output /path/to/your-resume-rebuilt.html
```

AI rewrite after configuring keys through environment variables or the app:

```bash
python3 resume_fixer.py --rebuild /path/to/your-resume.txt \
  --ai-rewrite \
  --target-role "Data Analyst" \
  --target-language English \
  --template masters
```

Use your own private resume path. Do not save a personal resume inside the
project folder or commit it to GitHub.

CLI credentials can use `RESUME_AI_API_KEY`, `RESUME_AI_BASE_URL`, and
`RESUME_AI_MODEL`. `OPENAI_API_KEY` and `OPENAI_BASE_URL` are also recognized.

## Formatting standards

| Template | Best for | Layout pattern |
| --- | --- | --- |
| `masters` | Early-career, master's, and standard professional resumes | Sans-serif; education first; uppercase headings; one page preferred |
| `phd` | Academic and research records with publications and teaching | Serif; formal research layout; awards, service, and publications included |
| `technical` | Technical research resumes where skills should appear early | Sans-serif; summary and skills near the top; publications and activities separated |

Use **Auto-detect** if unsure. All templates use consistent margins, section
rules, entry alignment, compact bullets, and print-safe spacing.

## What local "safe repair" changes

Without AI, the rebuild step may:

- Rename recognized headings to standard labels.
- Put sections into the selected template's order.
- Normalize bullet markers and whitespace.
- Fix capitalization for common tool names.
- Remove generic title lines such as `Resume` or `CV`.
- Align organization, role, location, and dates consistently.

It does not translate, rewrite meaning, or add missing results.

## Requirements and limitations

- macOS is recommended because PDF extraction uses Apple's PDFKit.
- Python 3.10 or newer is required. No third-party Python packages are needed.
- HTTPS uses the Mac system CA bundle when Python has no certificate store.
  A VPN/proxy root certificate can be supplied as an optional PEM file in AI
  settings; certificate verification is never disabled.
- AI mode requires internet access, a provider account, and API usage credit.
- Scanned/image-only PDFs need OCR, which is not implemented yet.
- Multi-column PDFs may extract in the wrong order.
- Unusual custom section headings may need to be renamed.
- Chinese headings can be standardized; Chinese body text requires AI mode for
  translation.
- There is no DOCX export or native one-click PDF export yet. Use the browser's
  print dialog.
- The review engine cannot verify whether a statement is true.

## Troubleshooting

### `Address already in use`

An older Resume Fixer process is still running. This version stops older
Resume Fixer servers when launched through `Start Resume Fixer.command`. If a
new launch says Resume Fixer is already running, use the existing Terminal
window and browser tab. Only one server is allowed so the API-key state cannot
split between two ports.

If another non-Resume-Fixer application owns the port, choose another one:

```bash
python3 resume_fixer.py --serve --port 9000
```

### The result looks formatted but the wording did not change

AI rewrite was off. This is deliberate when no working provider and API key are
loaded. Open **AI settings**, choose the provider preset, paste the key, click
**Save & test connection**, then return to the resume page. The banner should
turn green and the button should say **Review, rewrite & format with AI**.

If you leave **Remember the key on this Mac** unchecked, the key disappears when
the app stops and a later launch will return to local-only mode.

### Save & test connection fails

Check the effective request URL shown in **AI settings**. For DeepSeek it should
be:

```text
https://api.deepseek.com/v1/chat/completions
```

The model should normally be `deepseek-chat`. After clicking **Save & test
connection**, open **Open local connection diagnostics** below the form. It
shows the sanitized HTTP or network error and never shows the API key.

Common causes are an invalid or expired key, no API balance, a model name the
account cannot use, a VPN/proxy blocking `api.deepseek.com`, or a provider URL
from a different service. Only one Resume Fixer server can run at a time, so a
new Terminal launch cannot create a second keyless session.

### `CERTIFICATE_VERIFY_FAILED` or `self-signed certificate in certificate chain`

This is a local HTTPS trust problem, not a DeepSeek key or model problem.
Resume Fixer loads `/etc/ssl/cert.pem` automatically when Python has no CA
certificates.

If a VPN, corporate proxy, or antivirus product intercepts HTTPS, it substitutes
its own root certificate. Export that trusted root as a `.pem`, `.cer`, `.crt`,
or `.der` file, import it in **AI settings → Import a CA certificate instead**,
save, and test again. Do not disable TLS verification. If a VPN or corporate
security filter such as FortiClient is installed, its root certificate in
Keychain Access is a likely source.

### The page still shows an old version

Close the old browser tab and launch Resume Fixer again. The version appears at
the top of the page and in the Terminal window. You can inspect the local
diagnostic endpoint at <http://127.0.0.1:8765/health>; it reports whether AI is
ready without exposing the key.

## Project structure

```text
resume-fixer/
├── resume_fixer.py          # CLI, review report, rebuild, and server entry point
├── resume_formatter.py      # Parser, templates, placeholders, and HTML renderer
├── resume_repair.py         # Formatting-only normalization and change log
├── resume_ai.py             # BYOK AI client, guarded prompt, and validation
├── resume_settings.py       # Local provider settings and key storage
├── resume_io.py             # TXT, Markdown, DOCX, and PDF text extraction
├── resume_web.py            # Local review, rewrite, settings, and rebuild pages
├── rules.md                 # Generic resume-review and rewrite rules
├── AI_SETUP.md              # Beginner BYOK provider setup and troubleshooting
├── rubric.json              # Scoring dimensions and detection rules
├── knowledge/               # Safe formatting notes; no resume samples
├── versions/                # Release snapshots
├── VERSION                  # Current release number
├── CHANGELOG.md             # Release history
├── PROJECT_NOTES.md         # Status and next steps for future sessions
└── Start Resume Fixer.command
```

## Versioning

Resume Fixer uses `MAJOR.MINOR.PATCH` version numbers. The live command remains
`resume_fixer.py`; release snapshots live in `versions/` and changes are
recorded in `CHANGELOG.md`.

## Uploading this project to GitHub

See [GITHUB_UPLOAD.md](GITHUB_UPLOAD.md). Never upload API keys, personal
resumes, generated PDFs, or the local `~/.resume-fixer` settings folder.

## Roadmap

- [ ] DOCX export and native PDF export.
- [ ] More provider adapters beyond OpenAI-compatible endpoints.
- [ ] OCR for scanned PDFs.
- [ ] Saved review history and before/after versions.
- [ ] Optional agentic fact-checking against user-provided evidence.

## License

No license has been chosen yet. Add a license before distributing or accepting
contributions. The MIT Career Handbook and its sample resumes remain the
property of their respective owners.
