# Resume Fixer v0.6.3

Released 2026-11-15.

## Fixed

- New API keys are remembered by default, while the checkbox can still be
  cleared for session-only use.
- Saving the DeepSeek preset normalizes the endpoint to
  `https://api.deepseek.com/v1` and the model to `deepseek-chat`.
- The settings page displays the exact effective request URL.
- Only one Resume Fixer server can run at a time. A second launch reports the
  existing version and URL rather than creating a second keyless session on
  another port.
- Provider failures now produce a sanitized local diagnostic log and a
  `/diagnostics` page. API keys are redacted; resume text is not logged.

## Files

- Live application: `resume_fixer.py`
- Complete release snapshot: `versions/v0.6.3/`
- Release archive: `~/Desktop/resume-fixer-v0.6.3.zip`
