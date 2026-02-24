from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import create_app
from src.database.models import User
from src.rules.depends import RefreshTokenContext, validate_access_token_and_user_exists, validate_refresh_token
import src.api.routes.users as users_routes


@dataclass
class DummySession:
    """Minimal async session stub for route logic unit tests."""

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def refresh(self, _obj) -> None:
        return None

    def add(self, _obj) -> None:
        return None


@asynccontextmanager
async def fake_db_session() -> AsyncIterator[DummySession]:
    yield DummySession()


def make_user() -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        mobile_number=9999999999,
        city="Test City",
        password_hash="hashed",
    )
    user.id = uuid4()
    user.role = "user"
    user.is_active = True
    user.is_verified = False
    user.created_at = datetime.now(timezone.utc)
    return user


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch):
    app = create_app()

    async def override_user():
        return make_user()

    async def override_refresh():
        return RefreshTokenContext(user=make_user(), refresh_token="refresh-token-12345")

    app.dependency_overrides[validate_access_token_and_user_exists] = override_user
    app.dependency_overrides[validate_refresh_token] = override_refresh

    monkeypatch.setattr(users_routes, "get_db_session", fake_db_session)

    return app


@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield client


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Write a plain-text report to tests/test_report.txt after pytest run."""
    report_path = Path(__file__).resolve().parent / "test_report.txt"
    stats = terminalreporter.stats
    passed = stats.get("passed", [])
    failed = stats.get("failed", [])
    skipped = stats.get("skipped", [])
    error = stats.get("error", [])

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"Exit status: {exitstatus}\n")
        handle.write(f"Passed: {len(passed)}\n")
        handle.write(f"Failed: {len(failed)}\n")
        handle.write(f"Errors: {len(error)}\n")
        handle.write(f"Skipped: {len(skipped)}\n")

        if failed:
            handle.write("\nFailures:\n")
            for rep in failed:
                handle.write(f"\n{rep.nodeid}\n")
                handle.write(rep.longreprtext)
                handle.write("\n")

        if error:
            handle.write("\nErrors:\n")
            for rep in error:
                handle.write(f"\n{rep.nodeid}\n")
                handle.write(rep.longreprtext)
                handle.write("\n")

        if passed:
            handle.write("\nPassed Tests:\n")
            for rep in passed:
                handle.write(f"{rep.nodeid}\n")

        if skipped:
            handle.write("\nSkipped Tests:\n")
            for rep in skipped:
                handle.write(f"{rep.nodeid}\n")
