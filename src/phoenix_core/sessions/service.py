from datetime import datetime, timezone
from phoenix_core.errors import AuthenticationError

class SessionService:
    def __init__(self, db):
        self.db = db

    def get_active(self, session_id):
        row = self.db.execute(
            "SELECT id, identity_id, token_hash, expires_at, status, created_at "
            "FROM sessions WHERE id=?",
            (str(session_id),),
        ).fetchone()
        if not row:
            raise AuthenticationError("Session not found.")
        if row["status"] != "ACTIVE":
            raise AuthenticationError("Session is not active.")

        expires = datetime.fromisoformat(row["expires_at"])
        if expires <= datetime.now(timezone.utc):
            self.db.execute(
                "UPDATE sessions SET status='EXPIRED' WHERE id=?",
                (str(session_id),),
            )
            self.db.commit()
            raise AuthenticationError("Session has expired.")
        return row

    def revoke(self, session_id) -> bool:
        cur = self.db.execute(
            "UPDATE sessions SET status='REVOKED' "
            "WHERE id=? AND status='ACTIVE'",
            (str(session_id),),
        )
        self.db.commit()
        return cur.rowcount == 1

    def revoke_all_for_identity(self, identity_id) -> int:
        cur = self.db.execute(
            "UPDATE sessions SET status='REVOKED' "
            "WHERE identity_id=? AND status='ACTIVE'",
            (str(identity_id),),
        )
        self.db.commit()
        return cur.rowcount


