"""Core authentication service for Phoenix V2.

This is intentionally provider-independent and contains no business-module
logic. Persistent user/company storage will be introduced by the Core identity
layer; this phase provides a secure bootstrap authentication boundary for the
System web application.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from typing import Dict, Optional


SESSION_COOKIE = "phoenix_session"
PBKDF2_ITERATIONS = 600_000


@dataclass(frozen=True)
class AuthenticatedUser:
    username: str
    display_name: str
    role: str


class AuthenticationService:
    """Authenticate configured bootstrap users and manage server-side sessions."""

    def __init__(
        self,
        *,
        username: str,
        password: str,
        display_name: str = "Phoenix Administrator",
        role: str = "Administrator",
    ) -> None:
        if not username or not password:
            raise ValueError("Authentication requires a non-empty username and password")
        self._username = username
        self._password_hash = _hash_password(password)
        self._display_name = display_name
        self._role = role
        self._sessions: Dict[str, AuthenticatedUser] = {}

    @classmethod
    def from_environment(cls) -> "AuthenticationService":
        username = os.getenv("PHOENIX_ADMIN_USERNAME", "admin")
        password = os.getenv("PHOENIX_ADMIN_PASSWORD")
        if not password:
            raise RuntimeError("PHOENIX_ADMIN_PASSWORD must be configured")
        return cls(
            username=username,
            password=password,
            display_name=os.getenv("PHOENIX_ADMIN_DISPLAY_NAME", "Phoenix Administrator"),
            role=os.getenv("PHOENIX_ADMIN_ROLE", "Administrator"),
        )

    def authenticate(self, username: str, password: str) -> Optional[AuthenticatedUser]:
        if not hmac.compare_digest(username, self._username):
            return None
        if not _verify_password(password, self._password_hash):
            return None
        return AuthenticatedUser(
            username=self._username,
            display_name=self._display_name,
            role=self._role,
        )

    def create_session(self, user: AuthenticatedUser) -> str:
        token = secrets.token_urlsafe(48)
        self._sessions[token] = user
        return token

    def get_user(self, token: Optional[str]) -> Optional[AuthenticatedUser]:
        if not token:
            return None
        return self._sessions.get(token)

    def revoke_session(self, token: Optional[str]) -> None:
        if token:
            self._sessions.pop(token, None)


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual, expected)
