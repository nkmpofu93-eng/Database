# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

A personal collection of job-application documents (CVs tailored to specific
employers/roles) for Nkosilathi Mpofu. There is no code, build, or test suite.

## Layout

All files live at the repo root:

- `*.docx` — editable CV sources (Word)
- `*.pdf` — exported/final CVs
- `README.md` — one-line description

## File naming

Use `Nkosilathi_Mpofu_<Company>_<Role>_CV.<ext>`, e.g.
`Nkosilathi_Mpofu_Barclays_CorporateBanking_CV.pdf`.
Older files use spaces or a ` copy` suffix; follow the underscore form for new
files and don't rename existing ones unless asked.

## Working with the documents

- Read `.docx` with `python-docx`; read `.pdf` with `pdfplumber` or `pypdf`
  (both are installed).
- When tailoring a CV for a new role, copy the closest existing CV rather than
  editing it in place, so each application keeps its own version.
- Keep facts consistent across CVs (dates, employers, qualifications); only
  the emphasis and wording should change per role.
- Never invent experience, qualifications, or contact details.

## Privacy

These files contain personal information. Don't upload, share, or publish
them to external services unless explicitly asked.
