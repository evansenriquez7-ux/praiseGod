"""
The silent-path scanner (§8's `silent_path_disposition_8`, plan step 0).

The subtle part is the DEFINITION of silent, and getting it wrong fails in both
directions. Too broad and the gate flags handlers that record a finding and then continue
-- the very pattern the H-01 work replaced `except: continue` WITH -- which trains people
to paper over correct code with markers and buries the real ones. Too narrow and a
genuinely dropped obligation goes uncounted.

Measured: the first version returned "continue" for any body CONTAINING a Continue and
reported 33 silent handlers. Narrowed to bodies that do NOTHING BUT leave, it reports 19,
and the 14 it stopped flagging are all record-then-continue handlers, §10's two new
obligation reporters among them.
"""

from __future__ import annotations

import ast

from tests.silent_path_inventory import (
    VALID_DISPOSITIONS,
    _disposition_in,
    _silent_body,
    build_report,
    scan,
)


def _handler(src: str) -> ast.ExceptHandler:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            return node
    raise AssertionError("no handler in source")


class TestWhatCountsAsSilent:
    def test_a_bare_continue_is_silent(self):
        assert _silent_body(_handler("try:\n    x=1\nexcept E:\n    continue\n")) == "continue"

    def test_a_bare_pass_is_silent(self):
        assert _silent_body(_handler("try:\n    x=1\nexcept E:\n    pass\n")) == "pass"

    def test_a_bare_return_is_silent(self):
        assert _silent_body(_handler("try:\n    x=1\nexcept E:\n    return\n")) == "return"

    def test_a_return_with_a_value_is_not_silent(self):
        """Returning something is a decision; returning nothing is a shrug."""
        assert _silent_body(_handler("try:\n    x=1\nexcept E:\n    return []\n")) == ""

    def test_record_then_continue_is_NOT_silent(self):
        """The named-failure pattern. Flagging it is the false positive that matters."""
        src = ("try:\n    x=1\nexcept E as exc:\n"
               "    found.append(f'{node}: generation raised {exc}')\n    continue\n")
        assert _silent_body(_handler(src)) == ""

    def test_log_then_pass_is_NOT_silent(self):
        src = "try:\n    x=1\nexcept E:\n    print('warn')\n    pass\n"
        assert _silent_body(_handler(src)) == ""

    def test_a_comment_only_body_is_still_silent(self):
        """A docstring or comment does not make a shrug into a decision."""
        src = "try:\n    x=1\nexcept E:\n    'why we skip'\n    continue\n"
        assert _silent_body(_handler(src)) == "continue"

    def test_a_reraise_is_not_silent(self):
        assert _silent_body(_handler("try:\n    x=1\nexcept E:\n    raise\n")) == ""


class TestDispositionMarkers:
    def test_each_valid_kind_is_recognised(self):
        for kind in VALID_DISPOSITIONS:
            src = f"try:\n    x=1\nexcept E:\n    # DISPOSITION: {kind} -- because\n    continue\n"
            node = _handler(src)
            got, note = _disposition_in(src.splitlines(), node)
            assert got == kind and note == "because"

    def test_an_unknown_kind_is_reported_as_invalid_not_accepted(self):
        src = "try:\n    x=1\nexcept E:\n    # DISPOSITION: whatever -- hmm\n    continue\n"
        got, _ = _disposition_in(src.splitlines(), _handler(src))
        assert got == "INVALID", "an unrecognised marker must not pass as a disposition"

    def test_a_missing_marker_is_unclassified(self):
        src = "try:\n    x=1\nexcept E:\n    continue\n"
        got, _ = _disposition_in(src.splitlines(), _handler(src))
        assert got == ""


class TestTheLiveTree:
    def test_every_silent_handler_is_classified(self):
        unclassified = [p for p in scan() if not p.disposition]
        assert unclassified == [], (
            "a silent handler with no disposition drops an obligation without a word; "
            f"unclassified: {[(p.file, p.line) for p in unclassified]}"
        )

    def test_no_marker_names_an_unknown_kind(self):
        assert [p for p in scan() if p.disposition == "INVALID"] == []

    def test_the_scan_is_deterministic(self):
        assert [(p.file, p.line) for p in scan()] == [(p.file, p.line) for p in scan()]

    def test_the_report_counts_match_the_scan(self):
        report = build_report()
        assert report["counts"]["silent_handlers"] == len(scan())
