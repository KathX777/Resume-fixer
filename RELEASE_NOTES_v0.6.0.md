# Resume Fixer v0.6.0

Released 2026-11-15.

## Main change

Resume Fixer can now perform an optional AI-assisted rewrite and translation
using a provider account supplied by the user.

## BYOK workflow

1. Open **AI settings** in the local app.
2. Enter an OpenAI-compatible API base URL, a model name, and the user's API
   key.
3. Save and test the connection.
4. Upload a resume and enable **AI rewrite**.
5. Optionally enter a target role and job description.
6. Review the original and rewritten scores, rewrite examples, warnings, and
   missing-fact questions.
7. Fill every highlighted `[[ADD: ...]]` or `[[CHECK: ...]]` prompt.
8. Print/save the formatted result as PDF or download it as HTML.

## Key handling

- No API key is bundled with the project.
- The key is stored only on the user's computer.
- A saved key goes in `~/.resume-fixer/credentials.json` with user-only
  permissions.
- An unsaved key stays in memory only.
- The repository, release archive, and `.gitignore` exclude key files.

## Guardrails

- The AI must preserve facts and must use placeholders for missing results.
- The app warns about new numeric values, missing contact details, and large
  length changes.
- The user must verify every AI-generated claim before using the resume.

## Files

- Live application: `resume_fixer.py`
- Complete release snapshot: `versions/v0.6.0/`
- Release archive: `~/Desktop/resume-fixer-v0.6.0.zip`
- AI setup guide: `AI_SETUP.md`
