"""
An isolated, network-free database for harness checks that must exercise real routes.

Why this exists
---------------
`validate_grade` (§10) opened `SessionLocal()` -- the CONFIGURED database, a Neon host
across the public internet -- and wrote a `StudentProfile` row into it. Two consequences,
both recorded as `H-01` in the hardening ledger:

  * **Phase 1's verdict depended on DNS.** On 2026-09-12 the same code crashed the whole
    aggregate run (`could not translate host name ... neon.tech`) in the morning and
    passed §10 in the afternoon, because the network happened to be up. That is
    non-determinism in a gate, which AGENTS.md Protocol 6 forbids outright. A gate whose
    answer depends on an external host is not a gate.
  * **Persistent shared learner state.** A row named `GraderGate_shared` accumulated
    attempts, mastery states and ELO drift in the real database on every run, so the
    check's own inputs changed over time and it polluted production data.

What this gives instead
-----------------------
A SQLite file in a temporary directory, created fresh and deleted on exit, bound into
`backend.app.database` at the ONE seam every caller passes through: `get_engine`'s cached
`_engine`/`_SessionFactory`. Overriding there covers FastAPI's `get_db` dependency and
every direct `SessionLocal()` call in services and routes alike, without a
`dependency_overrides` entry per route.

The socket guard is the other half. Rebinding the engine proves nothing on its own -- a
route that reaches out to Redis, an LLM, or a second database would still make the verdict
depend on the network. Inside the context manager any `socket.socket.connect` to a
non-loopback address raises `HermeticNetworkError` by name, so a future network dependency
becomes a loud named failure instead of a slow gate that sometimes passes.

KNOWN LIMITATIONS (Scaling Mandate 6)
-------------------------------------
  * The guard hooks `socket.socket.connect`/`connect_ex` and `socket.create_connection`.
    A library that opens a connection through a C extension bypassing those (none is used
    here today) would not be caught. Loopback is deliberately ALLOWED because
    `fastapi.testclient` uses it; a real local service listening on 127.0.0.1 would
    therefore be reachable.
  * SQLite is not PostgreSQL. Column types in `backend/app/models.py` are portable
    (Integer/String/Float/Boolean/DateTime/Text/JSON) and no route in this path issues
    raw dialect-specific SQL, but a future Postgres-only construct would fail here rather
    than in production -- loudly, which is the safe direction.
"""

from __future__ import annotations

import socket
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


class HermeticNetworkError(RuntimeError):
    """A hermetic block attempted an outbound network connection."""


def _is_loopback(address) -> bool:
    if not isinstance(address, (tuple, list)) or not address:
        return False
    host = address[0]
    if not isinstance(host, str):
        return False
    return host in ("127.0.0.1", "::1", "localhost", "0.0.0.0", "")


@contextmanager
def no_network() -> Iterator[None]:
    """Any outbound non-loopback connection inside this block raises by name."""
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_create = socket.create_connection

    def guard(target):
        raise HermeticNetworkError(
            f"hermetic block attempted an outbound network connection to {target!r}. "
            "A Phase 1 gate must not depend on an external host (H-01, Protocol 6)."
        )

    def _connect(self, address, *a, **kw):
        if not _is_loopback(address):
            guard(address)
        return real_connect(self, address, *a, **kw)

    def _connect_ex(self, address, *a, **kw):
        if not _is_loopback(address):
            guard(address)
        return real_connect_ex(self, address, *a, **kw)

    def _create_connection(address, *a, **kw):
        if not _is_loopback(address):
            guard(address)
        return real_create(address, *a, **kw)

    socket.socket.connect = _connect          # type: ignore[method-assign]
    socket.socket.connect_ex = _connect_ex    # type: ignore[method-assign]
    socket.create_connection = _create_connection  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket.connect = real_connect          # type: ignore[method-assign]
        socket.socket.connect_ex = real_connect_ex    # type: ignore[method-assign]
        socket.create_connection = real_create        # type: ignore[assignment]


@contextmanager
def hermetic_database(block_network: bool = True) -> Iterator[str]:
    """
    Bind `backend.app.database` to a throwaway SQLite file for the duration.

    Yields the sqlite URL. Restores the previous engine/session factory on exit and
    removes the file, so no learner state survives the block.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.app import database as db_mod
    from backend.app import models  # noqa: F401  -- registers every table on Base

    prev_engine = db_mod._engine
    prev_factory = db_mod._SessionFactory
    prev_url = db_mod.DATABASE_URL

    tmpdir = tempfile.mkdtemp(prefix="hermetic_db_")
    path = Path(tmpdir) / "hermetic.sqlite"
    url = f"sqlite:///{path}"

    engine = create_engine(url, connect_args={"check_same_thread": False})
    db_mod.Base.metadata.create_all(bind=engine)
    db_mod._engine = engine
    db_mod._SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_mod.DATABASE_URL = url

    net: Optional[object] = None
    try:
        if block_network:
            net = no_network()
            net.__enter__()  # type: ignore[attr-defined]
        yield url
    finally:
        if net is not None:
            net.__exit__(None, None, None)  # type: ignore[attr-defined]
        engine.dispose()
        db_mod._engine = prev_engine
        db_mod._SessionFactory = prev_factory
        db_mod.DATABASE_URL = prev_url
        try:
            path.unlink(missing_ok=True)
            Path(tmpdir).rmdir()
        except OSError:
            pass
