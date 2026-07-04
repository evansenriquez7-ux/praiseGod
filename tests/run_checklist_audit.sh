#!/usr/bin/env bash
# Runs the exhaustive checklist auditor inside the project's venv.
# Use this — NOT bare `python` — so transitive imports (e.g. fastapi) resolve.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="${ROOT}/.venv/bin/python"

if [[ ! -x "${VENV_PY}" ]]; then
  echo "ERROR: venv python not found at ${VENV_PY}" >&2
  echo "       Create the venv and pip install -r requirements.txt first." >&2
  exit 2
fi

cd "${ROOT}"

# Reap orphaned workers from a previous interrupted run before starting. A
# killed/Ctrl-C'd parallel run can leave ProcessPoolExecutor children alive
# (multiprocessing-fork), each pinned to a core and holding GBs of RAM, which
# starves this run of CPU. Kill only auditor-related processes, and print what
# we kill (AGENTS.md #4 — no silent skipping).
STALE_PIDS="$(pgrep -f 'exhaustive_checklist_auditor|multiprocessing.spawn' 2>/dev/null | grep -v "^$$\$" || true)"
if [[ -n "${STALE_PIDS}" ]]; then
  echo "[run_checklist_audit] Reaping orphaned auditor workers before start:" >&2
  # shellcheck disable=SC2086
  ps -o pid,etime,pcpu,command -p ${STALE_PIDS} 2>/dev/null >&2 || true
  # shellcheck disable=SC2086
  kill -9 ${STALE_PIDS} 2>/dev/null || true
  sleep 1
fi

PYTHONPATH="${ROOT}" "${VENV_PY}" -m tests.exhaustive_checklist_auditor "$@"
