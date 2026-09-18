import os
from typing import Optional

from phoenix_core.security.secrets import SecretResolver


class EnvironmentSecretResolver(SecretResolver):
    """
    Development/server implementation of the Core SecretResolver.

    Secrets are resolved from server-side environment variables.
    """

    def get_secret(self, name: str) -> Optional[str]:
        if not name or not name.strip():
            raise ValueError("Secret name cannot be empty")

        value = os.environ.get(name.strip())

        if value is None or value == "":
            return None

        return value
