# Resume Fixer v0.6.5

Released 2026-11-23.

## Added

- Added `rules.md`, a generic guidance file organized into Structure, Tone &
  Style, Action Verbs, and Formatting sections.
- AI rewrite now loads `rules.md` and places those rules at the start of the
  system prompt before sending any resume to the configured provider.

## Changed

- Removed the `examples/` folder and rebuilt sample resumes.
- Removed the duplicate `knowledge/handbook_patterns.md` prompt file.
- Updated README, setup, project notes, and GitHub upload instructions to stop
  referencing sample resumes.

## Privacy

- The release contains no personal resume data, names, schools, employers, or
  contact information from the original examples.
- API keys remain outside the release in `~/.resume-fixer/credentials.json`.

## Files

- Live application: `resume_fixer.py`
- Generic AI guidance: `rules.md`
- Complete release snapshot: `versions/v0.6.5/`
- Release archive: `~/Desktop/resume-fixer-v0.6.5.zip`
