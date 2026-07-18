# Documentation Rules (meta-rules)

Adopt these five rules repo-wide. They prevent documentation drift and compile-time bugs.

* **R1 — Docs describe; the harness enforces.** No doc may contain a "MUST" about pipeline behavior unless it names the specific validator/assertion that enforces it (e.g. `validate_matrix §1A`).
* **R2 — One source of truth per fact; everything else links.** A rule, bounds list, or registry lives in exactly one place (usually in code/data), and docs link to it.
* **R3 — Separate the three doc species.**
  * *Contracts* — binding behavior, each line paired with its enforcing check.
  * *Judgment guides* — items requiring human evaluation, producing committed evidence artifacts under `validation_reports/judgment/`.
  * *Explainers* — design rationale, containing no MUSTs.
* **R4 — Doc changes ship with their enforcement, atomically.** Changing a contract doc requires changing the corresponding validator/check in the same PR, and vice versa.
* **R5 — Agent-facing docs are budgeted.** Keep contract documents under ~80 lines.

Before creating any new `.md` in `docs/`, classify it as **contract**, **judgment**, or **explainer**, and obey that species' rules. New MUSTs require a same-PR enforcer.
