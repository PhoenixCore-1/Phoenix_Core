"""Application service for Phoenix internal communications."""

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID, uuid4

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.communications.contracts import RealtimeEvent, RealtimePublisher
from phoenix_core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from phoenix_core.infrastructure import SQLiteDatabase


class CommunicationsService:
    """Application service for tenant-scoped Phoenix internal communications.

    Core remains authoritative for permission decisions. Communications owns
    communication resources and their tenant/resource access checks.
    """

    CHANNEL_TYPES = {
        "DIRECT",
        "GROUP",
        "TEAM",
        "PROJECT",
        "MODULE",
        "ANNOUNCEMENT",
        "CUSTOM",
    }

    VISIBILITIES = {"PRIVATE", "ORG"}

    PRESENCE_STATUSES = {"ONLINE", "AWAY", "OFFLINE"}

    PERMISSION_CHANNEL_CREATE = "communications.channel.create"
    PERMISSION_CHANNEL_MANAGE_MEMBERS = "communications.channel.manage_members"
    PERMISSION_MESSAGE_SEND = "communications.message.send"
    PERMISSION_MESSAGE_REACT = "communications.message.react"
    PERMISSION_MESSAGE_READ = "communications.message.read"
    PERMISSION_PRESENCE_UPDATE = "communications.presence.update"

    def __init__(
        self,
        db: SQLiteDatabase,
        *,
        authorize: Callable[[UUID, UUID, str], bool] | None = None,
        audit_record: Callable[[AuditEvent], AuditEvent] | None = None,
        realtime_publisher: RealtimePublisher | None = None,
    ):
        self.db = db
        self._authorize = authorize
        self._audit_record = audit_record
        self._realtime_publisher = realtime_publisher

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _require_permission(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        permission: str,
    ) -> None:
        if self._authorize is None:
            raise AuthorizationError(
                "Communications authorization is not configured."
            )

        if not self._authorize(identity_id, organisation_id, permission):
            raise AuthorizationError(
                f"Permission denied: {permission}"
            )

    def _audit(
        self,
        *,
        action: str,
        organisation_id: UUID,
        identity_id: UUID,
        target_type: str | None = None,
        target_id: UUID | None = None,
    ) -> None:
        if self._audit_record is None:
            return

        self._audit_record(
            AuditEvent.create(
                action=action,
                organisation_id=organisation_id,
                identity_id=identity_id,
                target_type=target_type,
                target_id=target_id,
            )
        )

    def _publish(
        self,
        *,
        event_type: str,
        organisation_id: UUID,
        actor_identity_id: UUID,
        resource_type: str,
        resource_id: UUID,
        payload: dict,
    ) -> None:
        """Publish a transport-independent realtime event when configured."""
        if self._realtime_publisher is None:
            return

        self._realtime_publisher.publish(
            RealtimeEvent(
                event_type=event_type,
                organisation_id=organisation_id,
                actor_identity_id=actor_identity_id,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload,
            )
        )
    def _require_identity(self, identity_id: UUID) -> None:
        row = self.db.execute(
            "SELECT id FROM identities WHERE id=? AND status='ACTIVE'",
            (str(identity_id),),
        ).fetchone()
        if not row:
            raise AuthorizationError("Identity is not active.")

    def _require_org(self, identity_id: UUID, organisation_id: UUID) -> None:
        self._require_identity(identity_id)

        row = self.db.execute(
            """
            SELECT 1
            FROM organisation_memberships
            WHERE identity_id=?
              AND organisation_id=?
              AND status='ACTIVE'
            """,
            (str(identity_id), str(organisation_id)),
        ).fetchone()

        if not row:
            raise AuthorizationError(
                "Identity is not an active member of the organisation."
            )

    def _require_channel_member(
        self,
        channel_id: UUID,
        identity_id: UUID,
    ) -> UUID:
        self._require_identity(identity_id)

        row = self.db.execute(
            """
            SELECT c.organisation_id
            FROM channels c
            JOIN channel_members cm
              ON cm.channel_id=c.id
            WHERE c.id=?
              AND c.status='ACTIVE'
              AND cm.identity_id=?
              AND cm.status='ACTIVE'
            """,
            (str(channel_id), str(identity_id)),
        ).fetchone()

        if not row:
            raise AuthorizationError(
                "Identity does not have access to the channel."
            )

        return UUID(row["organisation_id"])

    def _get_channel_org(self, channel_id: UUID) -> UUID:
        row = self.db.execute(
            "SELECT organisation_id FROM channels WHERE id=?",
            (str(channel_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Channel not found.")

        return UUID(row["organisation_id"])

    def _validate_channel_inputs(
        self,
        channel_type: str,
        name: str,
        visibility: str,
    ) -> None:
        if channel_type not in self.CHANNEL_TYPES:
            raise ValidationError("Invalid channel type.")

        if visibility not in self.VISIBILITIES:
            raise ValidationError("Invalid channel visibility.")

        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Channel name is required.")

        if len(name.strip()) > 200:
            raise ValidationError("Channel name is too long.")

    def create_channel(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        channel_type: str,
        name: str,
        visibility: str = "PRIVATE",
    ):
        self._require_org(identity_id, organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_CHANNEL_CREATE,
        )
        self._validate_channel_inputs(channel_type, name, visibility)

        channel_id = uuid4()
        now = self._now()

        try:
            self.db.execute(
                """
                INSERT INTO channels
                (id, organisation_id, channel_type, name, visibility,
                 created_by_identity_id, status, created_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    str(channel_id),
                    str(organisation_id),
                    channel_type,
                    name.strip(),
                    visibility,
                    str(identity_id),
                    "ACTIVE",
                    now,
                ),
            )

            self.db.execute(
                """
                INSERT INTO channel_members
                (id, channel_id, identity_id, status, joined_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    str(uuid4()),
                    str(channel_id),
                    str(identity_id),
                    "ACTIVE",
                    now,
                ),
            )

            self.db.commit()

        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "A channel with this name already exists."
                ) from exc
            raise

        self._audit(
            action="CHANNEL_CREATED",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_type="CHANNEL",
            target_id=channel_id,
        )

        return self.get_channel(channel_id, identity_id)

    def get_channel(self, channel_id: UUID, identity_id: UUID):
        organisation_id = self._require_channel_member(
            channel_id,
            identity_id,
        )

        row = self.db.execute(
            """
            SELECT id, organisation_id, channel_type, name, direct_key,
                   visibility, created_by_identity_id, status, created_at
            FROM channels
            WHERE id=?
            """,
            (str(channel_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Channel not found.")

        if UUID(row["organisation_id"]) != organisation_id:
            raise AuthorizationError("Channel tenant boundary violation.")

        return dict(row)

    def _direct_key(
        self,
        identity_a: UUID,
        identity_b: UUID,
    ) -> str:
        """Return a deterministic participant-pair key for a direct channel."""
        ids = sorted(
            [str(identity_a), str(identity_b)]
        )
        return f"{ids[0]}:{ids[1]}"

    def create_direct_channel(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        target_identity_id: UUID,
    ):
        """Create a tenant-scoped one-to-one direct conversation.

        Direct conversations are represented by the existing channels
        authority. A deterministic participant key prevents duplicate
        direct channels for the same pair of identities within a tenant.
        """
        self._require_org(identity_id, organisation_id)
        self._require_org(target_identity_id, organisation_id)

        if identity_id == target_identity_id:
            raise ValidationError(
                "A direct conversation requires two different identities."
            )

        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_CHANNEL_CREATE,
        )

        direct_key = self._direct_key(
            identity_id,
            target_identity_id,
        )

        existing = self.db.execute(
            """
            SELECT id
            FROM channels
            WHERE organisation_id=?
              AND channel_type='DIRECT'
              AND direct_key=?
              AND status='ACTIVE'
            """,
            (
                str(organisation_id),
                direct_key,
            ),
        ).fetchone()

        if existing:
            raise ConflictError(
                "A direct conversation already exists for these identities."
            )

        channel_id = uuid4()
        now = self._now()

        try:
            self.db.execute(
                """
                INSERT INTO channels
                (id, organisation_id, channel_type, name, direct_key,
                 visibility, created_by_identity_id, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(channel_id),
                    str(organisation_id),
                    "DIRECT",
                    "Direct",
                    direct_key,
                    "PRIVATE",
                    str(identity_id),
                    "ACTIVE",
                    now,
                ),
            )

            self.db.execute(
                """
                INSERT INTO channel_members
                (id, channel_id, identity_id, status, joined_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    str(uuid4()),
                    str(channel_id),
                    str(identity_id),
                    "ACTIVE",
                    now,
                ),
            )

            self.db.execute(
                """
                INSERT INTO channel_members
                (id, channel_id, identity_id, status, joined_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    str(uuid4()),
                    str(channel_id),
                    str(target_identity_id),
                    "ACTIVE",
                    now,
                ),
            )

            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "A direct conversation already exists for these identities."
                ) from exc

            raise

        self._audit(
            action="DIRECT_CHANNEL_CREATED",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_type="CHANNEL",
            target_id=channel_id,
        )

        return self.get_channel(
            channel_id,
            identity_id,
        )
    def create_group_channel(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        name: str,
        member_identity_ids: list[UUID] | None = None,
        visibility: str = "PRIVATE",
    ):
        """Create a tenant-scoped group conversation.

        The actor is automatically included as an active member. Any
        additional members must already be active members of the same
        organisation. Channel and initial membership creation occur in
        one transaction so a failed member validation cannot leave a
        partially-created group.
        """
        self._require_org(identity_id, organisation_id)
        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_CHANNEL_CREATE,
        )

        self._validate_channel_inputs(
            "GROUP",
            name,
            visibility,
        )

        requested_members = list(member_identity_ids or [])

        all_member_ids = [identity_id, *requested_members]

        if len({str(member_id) for member_id in all_member_ids}) != len(
            all_member_ids
        ):
            raise ValidationError(
                "Group channel members must be unique."
            )

        for member_identity_id in requested_members:
            self._require_org(
                member_identity_id,
                organisation_id,
            )

        channel_id = uuid4()
        now = self._now()

        try:
            self.db.execute(
                """
                INSERT INTO channels
                (id, organisation_id, channel_type, name, direct_key,
                 visibility, created_by_identity_id, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(channel_id),
                    str(organisation_id),
                    "GROUP",
                    name.strip(),
                    None,
                    visibility,
                    str(identity_id),
                    "ACTIVE",
                    now,
                ),
            )

            for member_identity_id in all_member_ids:
                self.db.execute(
                    """
                    INSERT INTO channel_members
                    (id, channel_id, identity_id, status, joined_at)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        str(uuid4()),
                        str(channel_id),
                        str(member_identity_id),
                        "ACTIVE",
                        now,
                    ),
                )

            self.db.commit()

        except Exception as exc:
            self.db.rollback()

            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "A channel with this name already exists."
                ) from exc

            raise

        self._audit(
            action="GROUP_CHANNEL_CREATED",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_type="CHANNEL",
            target_id=channel_id,
        )

        return self.get_channel(
            channel_id,
            identity_id,
        )
    def add_member(
        self,
        channel_id: UUID,
        actor_identity_id: UUID,
        identity_id: UUID,
    ) -> None:
        organisation_id = self._require_channel_member(
            channel_id,
            actor_identity_id,
        )

        self._require_permission(
            actor_identity_id,
            organisation_id,
            self.PERMISSION_CHANNEL_MANAGE_MEMBERS,
        )

        self._require_org(identity_id, organisation_id)

        existing = self.db.execute(
            """
            SELECT id, status
            FROM channel_members
            WHERE channel_id=? AND identity_id=?
            """,
            (str(channel_id), str(identity_id)),
        ).fetchone()

        if existing and existing["status"] == "ACTIVE":
            raise ConflictError(
                "Identity is already a channel member."
            )

        now = self._now()

        try:
            if existing:
                self.db.execute(
                    """
                    UPDATE channel_members
                    SET status='ACTIVE', joined_at=?
                    WHERE id=?
                    """,
                    (now, existing["id"]),
                )
            else:
                self.db.execute(
                    """
                    INSERT INTO channel_members
                    (id, channel_id, identity_id, status, joined_at)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        str(uuid4()),
                        str(channel_id),
                        str(identity_id),
                        "ACTIVE",
                        now,
                    ),
                )

            self.db.commit()

        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Identity is already a channel member."
                ) from exc
            raise

        self._audit(
            action="CHANNEL_MEMBER_ADDED",
            organisation_id=organisation_id,
            identity_id=actor_identity_id,
            target_type="CHANNEL",
            target_id=channel_id,
        )

    def send_message(
        self,
        channel_id: UUID,
        sender_identity_id: UUID,
        content: str,
        parent_message_id: UUID | None = None,
        context_type: str | None = None,
        context_id: str | None = None,
    ):
        organisation_id = self._require_channel_member(
            channel_id,
            sender_identity_id,
        )

        self._require_permission(
            sender_identity_id,
            organisation_id,
            self.PERMISSION_MESSAGE_SEND,
        )

        if not isinstance(content, str) or not content.strip():
            raise ValidationError("Message content is required.")

        if len(content.strip()) > 10000:
            raise ValidationError("Message content is too long.")

        if context_type is None and context_id is not None:
            raise ValidationError(
                "Context type is required when context ID is supplied."
            )

        if context_type is not None and not str(context_type).strip():
            raise ValidationError("Context type cannot be empty.")

        if parent_message_id is not None:
            parent = self.db.execute(
                """
                SELECT channel_id
                FROM messages
                WHERE id=?
                  AND status<>'DELETED'
                """,
                (str(parent_message_id),),
            ).fetchone()

            if not parent:
                raise ValidationError(
                    "Parent message does not exist."
                )

            if parent["channel_id"] != str(channel_id):
                raise ValidationError(
                    "Parent message must belong to the channel."
                )

        message_id = uuid4()
        now = self._now()

        try:
            self.db.execute(
                """
                INSERT INTO messages
                (id, channel_id, sender_identity_id, content,
                 parent_message_id, context_type, context_id,
                 status, created_at, edited_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(message_id),
                    str(channel_id),
                    str(sender_identity_id),
                    content.strip(),
                    (
                        None
                        if parent_message_id is None
                        else str(parent_message_id)
                    ),
                    context_type.strip() if context_type else None,
                    context_id,
                    "ACTIVE",
                    now,
                    None,
                ),
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self._audit(
            action="MESSAGE_SENT",
            organisation_id=organisation_id,
            identity_id=sender_identity_id,
            target_type="MESSAGE",
            target_id=message_id,
        )

        return dict(
            self.db.execute(
                "SELECT * FROM messages WHERE id=?",
                (str(message_id),),
            ).fetchone()
        )

    def list_messages(
        self,
        channel_id: UUID,
        identity_id: UUID,
        limit: int = 50,
        before_id: UUID | None = None,
    ):
        organisation_id = self._require_channel_member(
            channel_id,
            identity_id,
        )

        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_MESSAGE_READ,
        )

        try:
            limit = int(limit)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Message limit must be an integer.") from exc

        if limit < 1 or limit > 200:
            raise ValidationError(
                "Message limit must be between 1 and 200."
            )

        params: list[str | int] = [str(channel_id)]

        if before_id is not None:
            cursor = self.db.execute(
                """
                SELECT created_at, id
                FROM messages
                WHERE id=? AND channel_id=?
                """,
                (str(before_id), str(channel_id)),
            ).fetchone()

            if not cursor:
                raise NotFoundError("Message cursor not found.")

            sql = """
                SELECT *
                FROM messages
                WHERE channel_id=?
                  AND status<>'DELETED'
                  AND (
                      created_at < ?
                      OR (created_at = ? AND id < ?)
                  )
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            """
            params.extend(
                [
                    cursor["created_at"],
                    cursor["created_at"],
                    cursor["id"],
                    limit,
                ]
            )
        else:
            sql = """
                SELECT *
                FROM messages
                WHERE channel_id=?
                  AND status<>'DELETED'
                ORDER BY created_at DESC, id DESC
                LIMIT ?
            """
            params.append(limit)

        return [
            dict(row)
            for row in self.db.execute(sql, params).fetchall()
        ]

    def add_reaction(
        self,
        message_id: UUID,
        identity_id: UUID,
        reaction: str,
    ) -> None:
        row = self.db.execute(
            """
            SELECT m.channel_id, c.organisation_id
            FROM messages m
            JOIN channels c ON c.id=m.channel_id
            WHERE m.id=?
              AND m.status<>'DELETED'
              AND c.status='ACTIVE'
            """,
            (str(message_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("Message not found.")

        channel_id = UUID(row["channel_id"])
        organisation_id = UUID(row["organisation_id"])

        self._require_channel_member(channel_id, identity_id)
        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_MESSAGE_REACT,
        )

        if not isinstance(reaction, str) or not reaction.strip():
            raise ValidationError("Reaction is required.")

        if len(reaction.strip()) > 100:
            raise ValidationError("Reaction is too long.")

        try:
            self.db.execute(
                """
                INSERT INTO message_reactions
                (id, message_id, identity_id, reaction, created_at)
                VALUES (?,?,?,?,?)
                """,
                (
                    str(uuid4()),
                    str(message_id),
                    str(identity_id),
                    reaction.strip(),
                    self._now(),
                ),
            )
            self.db.commit()

        except Exception as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                raise ConflictError(
                    "Reaction already exists."
                ) from exc
            raise

        self._audit(
            action="MESSAGE_REACTION_ADDED",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_type="MESSAGE",
            target_id=message_id,
        )

    def mark_read(
        self,
        channel_id: UUID,
        identity_id: UUID,
        message_id: UUID | None = None,
    ) -> None:
        organisation_id = self._require_channel_member(
            channel_id,
            identity_id,
        )

        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_MESSAGE_READ,
        )

        if message_id is not None:
            row = self.db.execute(
                """
                SELECT id
                FROM messages
                WHERE id=?
                  AND channel_id=?
                  AND status<>'DELETED'
                """,
                (str(message_id), str(channel_id)),
            ).fetchone()

            if not row:
                raise ValidationError(
                    "Read message must belong to the channel."
                )

        now = self._now()

        self.db.execute(
            """
            INSERT INTO message_read_states
            (channel_id, identity_id, last_read_message_id, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(channel_id,identity_id)
            DO UPDATE SET
                last_read_message_id=excluded.last_read_message_id,
                updated_at=excluded.updated_at
            """,
            (
                str(channel_id),
                str(identity_id),
                None if message_id is None else str(message_id),
                now,
            ),
        )
        self.db.commit()

        self._audit(
            action="MESSAGE_READ",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_type="CHANNEL",
            target_id=channel_id,
        )

    def set_presence(
        self,
        identity_id: UUID,
        organisation_id: UUID,
        status: str,
    ) -> None:
        self._require_org(identity_id, organisation_id)

        if status not in self.PRESENCE_STATUSES:
            raise ValidationError("Invalid presence status.")

        self._require_permission(
            identity_id,
            organisation_id,
            self.PERMISSION_PRESENCE_UPDATE,
        )

        self.db.execute(
            """
            INSERT INTO presence_states
            (organisation_id, identity_id, status, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(organisation_id,identity_id)
            DO UPDATE SET
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                str(organisation_id),
                str(identity_id),
                status,
                self._now(),
            ),
        )
        self.db.commit()

        self._audit(
            action="PRESENCE_CHANGED",
            organisation_id=organisation_id,
            identity_id=identity_id,
            target_type="IDENTITY",
            target_id=identity_id,
        )

    def get_presence(
        self,
        requester_identity_id: UUID,
        target_identity_id: UUID,
        organisation_id: UUID,
    ):
        self._require_org(requester_identity_id, organisation_id)
        self._require_org(target_identity_id, organisation_id)

        row = self.db.execute(
            """
            SELECT organisation_id,identity_id,status,updated_at
            FROM presence_states
            WHERE organisation_id=? AND identity_id=?
            """,
            (
                str(organisation_id),
                str(target_identity_id),
            ),
        ).fetchone()

        return dict(row) if row else None
