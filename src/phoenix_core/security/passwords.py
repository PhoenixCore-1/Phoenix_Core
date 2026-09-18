"""Password hashing primitives.

Uses Python's standard-library scrypt implementation so the initial Core V2
foundation has no third-party runtime dependency.
"""

import base64
import hashlib
import hmac
import os

_PREFIX = "scrypt$"
_N = 2**14
_R = 8
_P = 1
_DKLEN = 32

def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_N,
        r=_R,
        p=_P,
        dklen=_DKLEN,
    )
    return (
        f"{_PREFIX}{_N}${_R}${_P}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(digest).decode()}"
    )

def verify_password(password: str, encoded: str) -> bool:
    try:
        prefix, n, r, p, salt_b64, digest_b64 = encoded.split("$")
        if prefix != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
