"""
The isolated database fixture, pinned in both directions.

`H-01` was not "§10 crashes sometimes". It was that §10's verdict depended on whether an
external host resolved: the same code crashed Phase 1 on Neon DNS in the morning of
2026-09-12 and passed in the afternoon. A fixture that silently fell back to the
configured database would restore exactly that, and it would do so QUIETLY -- the check
would still pass, just against the wrong database. So both halves are asserted here:
the rebinding really happens, and the network guard really refuses.
"""

from __future__ import annotations

import socket

import pytest

from backend.app import database as db_mod
from tests.hermetic_db import HermeticNetworkError, hermetic_database, no_network


class TestEngineRebinding:
    def test_session_is_bound_to_a_throwaway_sqlite_file(self):
        with hermetic_database() as url:
            assert url.startswith("sqlite:///")
            session = db_mod.SessionLocal()
            try:
                assert session.get_bind().url.get_backend_name() == "sqlite"
            finally:
                session.close()

    def test_tables_exist_and_a_learner_round_trips(self):
        from backend.app.models import StudentProfile
        with hermetic_database():
            session = db_mod.SessionLocal()
            try:
                learner = StudentProfile(name="pinned", pin_hash="x", age=8, grade=3,
                                         language_preference="en")
                session.add(learner)
                session.commit()
                session.refresh(learner)
                assert learner.id is not None
            finally:
                session.close()

    def test_nothing_survives_the_block(self):
        """Two blocks are two databases; a shared learner would be persistent state."""
        from backend.app.models import StudentProfile
        ids = []
        for _ in range(2):
            with hermetic_database():
                session = db_mod.SessionLocal()
                try:
                    session.add(StudentProfile(name="same_name", pin_hash="x", age=8,
                                               grade=3, language_preference="en"))
                    session.commit()
                    ids.append(session.query(StudentProfile).count())
                finally:
                    session.close()
        assert ids == [1, 1], "the second block must start empty, not inherit the first"

    def test_the_previous_engine_is_restored_on_exit(self):
        before = db_mod._engine
        with hermetic_database():
            assert db_mod._engine is not before
        assert db_mod._engine is before

    def test_the_engine_is_restored_even_when_the_block_raises(self):
        before = db_mod._engine
        with pytest.raises(ValueError):
            with hermetic_database():
                raise ValueError("boom")
        assert db_mod._engine is before


class TestNetworkGuard:
    def test_an_outbound_connection_raises_by_name(self):
        with no_network():
            with pytest.raises(HermeticNetworkError):
                socket.create_connection(("example.com", 80), timeout=1)

    def test_socket_connect_is_guarded_too(self):
        with no_network():
            sock = socket.socket()
            try:
                with pytest.raises(HermeticNetworkError):
                    sock.connect(("example.com", 80))
            finally:
                sock.close()

    def test_connect_ex_is_guarded_too(self):
        with no_network():
            sock = socket.socket()
            try:
                with pytest.raises(HermeticNetworkError):
                    sock.connect_ex(("example.com", 80))
            finally:
                sock.close()

    def test_loopback_stays_reachable_because_testclient_needs_it(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        try:
            with no_network():
                client = socket.create_connection(("127.0.0.1", port), timeout=2)
                client.close()
        finally:
            listener.close()

    def test_the_guard_is_removed_on_exit(self):
        before = socket.socket.connect
        with no_network():
            assert socket.socket.connect is not before
        assert socket.socket.connect is before

    def test_the_guard_is_removed_even_when_the_block_raises(self):
        before = socket.create_connection
        with pytest.raises(ValueError):
            with no_network():
                raise ValueError("boom")
        assert socket.create_connection is before
