# Resume Fixer v0.6.2

Released 2026-11-15.

## Fixed

- The upload page now clearly distinguishes local formatting from AI rewriting.
  When no working provider and key are loaded, it displays **AI rewrite is OFF**
  and changes the button to **Review & format locally**.
- Local-only results say **Local formatting complete — text was not rewritten**
  instead of implying that the wording changed.
- The running version is visible on the page and in the Terminal.
- The launcher stops older Resume Fixer servers before starting the current
  version, which prevents an old tab or fallback port from hiding an update.
- The DeepSeek preset uses `https://api.deepseek.com/v1` and `deepseek-chat`.
  The common mistaken value `Deepseek` is corrected when settings are saved.
- The settings page warns when no API key is loaded and explains the difference
  between a remembered key and a session-only key.

## Added

- `/health` local diagnostic endpoint reporting version, provider, model, port,
  and AI readiness without exposing the API key.

## Files

- Live application: `resume_fixer.py`
- Complete release snapshot: `versions/v0.6.2/`
- Release archive: `~/Desktop/resume-fixer-v0.6.2.zip`
