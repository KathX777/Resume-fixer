# Upload Resume Fixer to GitHub

This is a beginner checklist. You do not need to know Git commands to publish
the first copy.

## Before uploading

Do **not** upload:

- Your real resume (`.docx`, `.pdf`, or copied text).
- Generated resume PDFs or saved HTML files containing personal information.
- API keys, `.env` files, `config.json`, `credentials.json`, or anything from
  `~/.resume-fixer`.
- The `__pycache__` folder.
- `.DS_Store` files.

No sample resumes are shipped with this version. Do not add personal resumes to
the repository.

## Create the repository

1. Sign in at <https://github.com>.
2. Click **+** in the top-right corner, then **New repository**.
3. Name it `resume-fixer`.
4. Add a short description: `Local-first resume review, BYOK AI rewrite, and formatting tool`.
5. Choose **Private** while you are still experimenting. You can make it public
   later in **Settings > General > Danger Zone**.
6. Do **not** add another README, `.gitignore`, or license on the GitHub page,
   because this folder already contains them.
7. Click **Create repository**.

## Upload the files

1. On the new repository page, click **uploading an existing file**.
2. Open `~/resume-fixer` in Finder.
   Press **Command + Shift + .** if you want to see hidden files such as
   `.gitignore`.
3. Drag these items into the GitHub upload page:
   - `README.md`
   - `AI_SETUP.md`
   - `GITHUB_UPLOAD.md`
   - `CHANGELOG.md`
   - `PROJECT_NOTES.md`
   - `RELEASE_NOTES_v0.6.7.md`
   - `VERSION`
   - `rules.md`
   - `rubric.json`
   - `resume_fixer.py`
   - `resume_formatter.py`
   - `resume_repair.py`
   - `resume_ai.py`
   - `resume_settings.py`
   - `resume_io.py`
   - `resume_web.py`
   - `Start Resume Fixer.command`
   - `.gitignore` (optional but recommended)
   - the `knowledge` folder
4. Do not drag `__pycache__`.
5. Do not drag the `versions` folder; older snapshots may contain retired
   example files.
6. In the commit message, write `Release v0.6.7`.
7. Click **Commit changes**.

## Check the README

The repository home page should show the Resume Fixer README. If it does not,
open `README.md`, click the pencil icon, and make sure the file is named exactly
`README.md`.

## For future updates

Use one of these approaches:

- **GitHub website:** open the changed file, click the pencil, paste the new
  content, and commit.
- **GitHub Desktop:** install it from <https://desktop.github.com>, clone the
  repository, copy updated files into the folder, commit, and push.
- **Command line:** use Git after you are comfortable with it.

Before every release:

1. Update `VERSION`.
2. Add an entry to `CHANGELOG.md`.
3. Run `python3 -m py_compile *.py`.
4. Test the launcher and one review.
5. Update `PROJECT_NOTES.md`.

## Important for other users

Each user must connect their own AI provider through the app's **AI settings**
page. Never add your own key to the repository to make AI work for everyone.
The app also works without AI in local review and formatting mode.

## If GitHub asks about a license

This project does not have a license yet. Learn about the options at
<https://choosealicense.com>. A common choice for a small open-source project
is the MIT License, but choose deliberately before making the project public.
