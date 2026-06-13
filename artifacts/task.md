# Vocabulary Audit & Cleanup Tasks

- `[ ]` Phase 1: Automated Language Audit
  - `[ ]` Write audit script `scratch/audit_vocabulary.py`
  - `[ ]` Run audit script to scan all nodes, formatters, and contexts
  - `[ ]` Generate `vocabulary_audit_report.md` in `artifacts/`
- `[ ]` Phase 2: Vocabulary Cleanup and Surgical Fixes
  - `[ ]` Apply fixes to identified DNA files and formatters based on the report
  - `[ ]` Re-run audit script to confirm zero occurrences of grade-inappropriate language
- `[ ]` Phase 3: Verification & Walkthrough
  - `[ ]` Run unit tests with `PYTHONPATH=. ./venv/bin/pytest backend/app/practice_gen/`
  - `[ ]` Update `walkthrough.md` in `artifacts/` with details of vocabulary changes
