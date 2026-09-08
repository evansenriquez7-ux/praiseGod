"""
test_frontier_query_count.py
============================
Pins the query cost of `check_and_advance_subject_frontier` against a student's
mastery-state count.

Why it exists
-------------
The function ran `db.query(SkillNode).filter(SkillNode.id == s.skill_id).first()`
once per mastery state, in three separate loops. That is an N+1 on the answer
submission hot path -- every answer a student submits pays one round trip per skill
they have ever touched.

Measured against the live (remote) database before the fix:

    fresh student   (0 mastery states)     9 queries    1.04s
    shared student  (151 mastery states) 163 queries   12.12s
    after the fix   (151 mastery states)  13 queries    1.67s

At the ~79 ms round-trip this deployment sees, 152 extra queries is ~12 seconds of
pure latency per submitted answer. It surfaced as §10 appearing to hang -- the gate
exercises all 151 nodes under one shared student, so each run made the next slower.
Real grade 4-10 students accumulate states the same way; this is a serving defect,
not a test artifact.

The assertion is on query COUNT, not wall-clock: latency varies with the network,
the N+1 does not.
"""

import os
import sys

import pytest
import sqlalchemy
from sqlalchemy import event

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _REPO_ROOT)


class _QueryCounter:
    def __init__(self):
        self.n = 0

    def __enter__(self):
        self._h = lambda *a, **k: setattr(self, "n", self.n + 1)
        event.listen(sqlalchemy.engine.Engine, "before_cursor_execute", self._h)
        self.n = 0
        return self

    def __exit__(self, *exc):
        event.remove(sqlalchemy.engine.Engine, "before_cursor_execute", self._h)
        return False


# The fix issues ONE bulk SkillNode fetch plus the function's own fixed queries.
# Before the fix this grew by one per mastery state (151 states -> 152 extra).
_MAX_QUERIES = 12


@pytest.mark.parametrize("n_states", [0, 5, 40])
def test_query_count_does_not_scale_with_mastery_states(n_states, monkeypatch):
    """
    The whole point: cost must be flat in the number of mastery states.

    Driven through fakes rather than the live database -- the assertion is about how
    many queries the function issues, which does not need a network round trip to
    observe, and the remote DB would make this test minutes long.
    """
    from backend.app.services import curriculum

    class _FakeNode:
        def __init__(self, i):
            self.id = i
            self.grade_level = "3"
            self.subject = "math"

    class _FakeState:
        def __init__(self, i):
            self.skill_id = i
            self.status = "active"

    states = [_FakeState(i) for i in range(n_states)]
    nodes = [_FakeNode(i) for i in range(n_states)]
    calls = {"n": 0}

    class _Q:
        def __init__(self, model):
            self._model = model

        def join(self, *a, **k):
            return self

        def filter(self, *a, **k):
            return self

        def all(self):
            calls["n"] += 1
            from backend.app import models
            return states if self._model is models.MasteryState else nodes

        def first(self):
            calls["n"] += 1
            return nodes[0] if nodes else None

    class _DB:
        def query(self, model):
            return _Q(model)

        def commit(self):
            pass

    curriculum.check_and_advance_subject_frontier(student_id=1, subject="math", db=_DB())

    assert calls["n"] <= _MAX_QUERIES, (
        f"{calls['n']} queries for {n_states} mastery states (cap {_MAX_QUERIES}). "
        f"The per-state SkillNode lookup has returned -- this is an N+1 on the answer "
        f"submission path and costs one network round trip per skill the student has "
        f"touched."
    )
