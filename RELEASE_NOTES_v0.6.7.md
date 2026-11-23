# Resume Fixer v0.6.7

Released 2026-11-23.

## Added

- **Tailor to a specific company** panel on the result page.
- Large text input for company values, recruiter guidance, role requirements,
  or a job description.
- Separate AI refinement call using the current revised resume and the pasted
  company guidance.
- Side-by-side comparison of the current and tailored resumes.
- **Use tailored version** and **Keep current version** controls.

## Behavior

- Tailoring aligns keywords, tone, and emphasis while instructing the model not
  to change the resume's overall format.
- The current resume is preserved until the user chooses the tailored version.
- Refinement errors are shown on the result page without losing the current
  resume or the pasted guidance.

## Files

- Live application: `resume_fixer.py`
- Generic AI guidance: `rules.md`
- Complete release snapshot: `versions/v0.6.7/`
- Release archive: `~/Desktop/resume-fixer-v0.6.7.zip`
