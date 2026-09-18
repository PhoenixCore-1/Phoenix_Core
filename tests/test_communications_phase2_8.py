import pytest
from uuid import uuid4

from phoenix_core.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.services import CoreFoundationService


COMMUNICATION_PERMISSIONS = [
    "communications.channel.create",
    "communications.channel.manage_members",
    "communications.message.send",
    "communications.message.react",
    "communications.message.read",
    "communications.presence.update",
]


def make_service(tmp_path):
    db = SQLiteDatabase(tmp_path / "test.db")
    service = CoreFoundationService(db)
    service.initialise()
    return db, service


def setup_company(service):
    org = service.create_organisation("C1", "Company")
    user1 = service.create_user("u1", "User 1", "Correct-Horse-Battery")
    user2 = service.create_user("u2", "User 2", "Correct-Horse-Battery")

    membership1 = service.add_membership(user1.identity_id, org.id)
    membership2 = service.add_membership(user2.identity_id, org.id)

    role = service.create_role(
        org.id,
        "communications_test_role",
        "Communications Test Role",
    )

    for permission_code in COMMUNICATION_PERMISSIONS:
        permission = service.get_permission_by_code(permission_code)
        assert permission is not None
        service.grant_permission(role.id, permission.id)

    service.assign_role(membership1.id, role.id)
    service.assign_role(membership2.id, role.id)

    return org, user1, user2


def test_channel_and_membership_and_tenant_isolation(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        channel = communications.create_channel(
            user1.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        communications.add_member(
            channel["id"],
            user1.identity_id,
            user2.identity_id,
        )

        assert communications.get_channel(
            channel["id"],
            user2.identity_id,
        )["name"] == "Engineering"

        other_org = core.create_organisation("C2", "Other")
        other_user = core.create_user(
            "u3",
            "User 3",
            "Correct-Horse-Battery",
        )
        core.add_membership(other_user.identity_id, other_org.id)

        with pytest.raises(AuthorizationError):
            communications.get_channel(
                channel["id"],
                other_user.identity_id,
            )
    finally:
        db.close()


def test_messages_threads_reactions_and_read(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        channel = communications.create_channel(
            user1.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        communications.add_member(
            channel["id"],
            user1.identity_id,
            user2.identity_id,
        )

        message = communications.send_message(
            channel["id"],
            user1.identity_id,
            "Hello",
        )

        reply = communications.send_message(
            channel["id"],
            user2.identity_id,
            "Reply",
            parent_message_id=message["id"],
        )

        communications.add_reaction(
            message["id"],
            user2.identity_id,
            "thumbsup",
        )

        communications.mark_read(
            channel["id"],
            user2.identity_id,
            reply["id"],
        )

        assert reply["parent_message_id"] == message["id"]

        row = db.execute(
            "SELECT count(*) AS count FROM message_reactions"
        ).fetchone()

        assert row["count"] == 1
    finally:
        db.close()


def test_invalid_message_inputs(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, _ = setup_company(core)

        channel = communications.create_channel(
            user1.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        with pytest.raises(ValidationError):
            communications.send_message(
                channel["id"],
                user1.identity_id,
                "   ",
            )

        with pytest.raises(ValidationError):
            communications.send_message(
                channel["id"],
                user1.identity_id,
                "reply",
                parent_message_id=uuid4(),
            )
    finally:
        db.close()


def test_duplicate_members_and_reactions(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        channel = communications.create_channel(
            user1.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        communications.add_member(
            channel["id"],
            user1.identity_id,
            user2.identity_id,
        )

        with pytest.raises(ConflictError):
            communications.add_member(
                channel["id"],
                user1.identity_id,
                user2.identity_id,
            )

        message = communications.send_message(
            channel["id"],
            user1.identity_id,
            "Hello",
        )

        communications.add_reaction(
            message["id"],
            user2.identity_id,
            "like",
        )

        with pytest.raises(ConflictError):
            communications.add_reaction(
                message["id"],
                user2.identity_id,
                "like",
            )
    finally:
        db.close()


def test_presence(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, _ = setup_company(core)

        communications.set_presence(
            user1.identity_id,
            org.id,
            "ONLINE",
        )

        assert communications.get_presence(
            user1.identity_id,
            user1.identity_id,
            org.id,
        )["status"] == "ONLINE"
    finally:
        db.close()

def test_permission_enforcement(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org = core.create_organisation("C1", "Company")
        user = core.create_user(
            "u1",
            "User 1",
            "Correct-Horse-Battery",
        )
        membership = core.add_membership(user.identity_id, org.id)

        role = core.create_role(
            org.id,
            "communications_limited_role",
            "Communications Limited Role",
        )
        core.assign_role(membership.id, role.id)

        communications = core.communications_service

        with pytest.raises(AuthorizationError):
            communications.create_channel(
                user.identity_id,
                org.id,
                "TEAM",
                "Engineering",
            )

        permission = core.get_permission_by_code(
            "communications.channel.create"
        )
        core.grant_permission(role.id, permission.id)

        channel = communications.create_channel(
            user.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        with pytest.raises(AuthorizationError):
            communications.send_message(
                channel["id"],
                user.identity_id,
                "Should fail",
            )

        permission = core.get_permission_by_code(
            "communications.message.send"
        )
        core.grant_permission(role.id, permission.id)

        message = communications.send_message(
            channel["id"],
            user.identity_id,
            "Should work",
        )

        with pytest.raises(AuthorizationError):
            communications.add_reaction(
                message["id"],
                user.identity_id,
                "like",
            )

    finally:
        db.close()


def test_presence_is_tenant_scoped(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org1 = core.create_organisation("C1", "Company 1")
        org2 = core.create_organisation("C2", "Company 2")

        user = core.create_user(
            "u1",
            "User 1",
            "Correct-Horse-Battery",
        )

        membership = core.add_membership(
            user.identity_id,
            org1.id,
        )

        role = core.create_role(
            org1.id,
            "presence_role",
            "Presence Role",
        )

        permission = core.get_permission_by_code(
            "communications.presence.update"
        )
        core.grant_permission(role.id, permission.id)
        core.assign_role(membership.id, role.id)

        communications = core.communications_service

        communications.set_presence(
            user.identity_id,
            org1.id,
            "ONLINE",
        )

        assert communications.get_presence(
            user.identity_id,
            user.identity_id,
            org1.id,
        )["status"] == "ONLINE"

        with pytest.raises(AuthorizationError):
            communications.get_presence(
                user.identity_id,
                user.identity_id,
                org2.id,
            )

    finally:
        db.close()


def test_communications_write_operations_create_audit_events(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org, user1, user2 = setup_company(core)
        communications = core.communications_service

        channel = communications.create_channel(
            user1.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        communications.add_member(
            channel["id"],
            user1.identity_id,
            user2.identity_id,
        )

        message = communications.send_message(
            channel["id"],
            user1.identity_id,
            "Audit me",
        )

        communications.add_reaction(
            message["id"],
            user2.identity_id,
            "like",
        )

        communications.mark_read(
            channel["id"],
            user2.identity_id,
            message["id"],
        )

        communications.set_presence(
            user1.identity_id,
            org.id,
            "ONLINE",
        )

        events = core.list_audit_events(
            organisation_id=org.id,
            limit=100,
        )

        actions = {event.action for event in events}

        assert "CHANNEL_CREATED" in actions
        assert "CHANNEL_MEMBER_ADDED" in actions
        assert "MESSAGE_SENT" in actions
        assert "MESSAGE_REACTION_ADDED" in actions
        assert "MESSAGE_READ" in actions
        assert "PRESENCE_CHANGED" in actions

    finally:
        db.close()

def test_message_pagination_before_id(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, _ = setup_company(core)

        channel = communications.create_channel(
            user1.identity_id,
            org.id,
            "TEAM",
            "Engineering",
        )

        messages = []

        for content in ("Message 1", "Message 2", "Message 3", "Message 4"):
            messages.append(
                communications.send_message(
                    channel["id"],
                    user1.identity_id,
                    content,
                )
            )

        latest = communications.list_messages(
            channel["id"],
            user1.identity_id,
            limit=2,
        )

        assert len(latest) == 2

        cursor = latest[-1]["id"]

        older = communications.list_messages(
            channel["id"],
            user1.identity_id,
            limit=2,
            before_id=cursor,
        )

        latest_ids = {row["id"] for row in latest}
        older_ids = {row["id"] for row in older}

        assert latest_ids.isdisjoint(older_ids)

        assert len(older) == 2

        assert older[0]["content"] == "Message 2"
        assert older[1]["content"] == "Message 1"

        with pytest.raises(Exception):
            communications.list_messages(
                channel["id"],
                user1.identity_id,
                before_id=uuid4(),
            )

    finally:
        db.close()
def test_direct_channel_creation_and_membership(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        channel = communications.create_direct_channel(
            user1.identity_id,
            org.id,
            user2.identity_id,
        )

        assert channel["channel_type"] == "DIRECT"
        assert channel["visibility"] == "PRIVATE"
        assert channel["direct_key"]

        members = db.execute(
            """
            SELECT identity_id
            FROM channel_members
            WHERE channel_id=?
              AND status='ACTIVE'
            ORDER BY identity_id
            """,
            (channel["id"],),
        ).fetchall()

        assert {row["identity_id"] for row in members} == {
            str(user1.identity_id),
            str(user2.identity_id),
        }
        assert len(members) == 2

        assert communications.get_channel(
            channel["id"],
            user2.identity_id,
        )["id"] == channel["id"]

    finally:
        db.close()


def test_direct_channel_duplicate_pair_is_rejected(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        first = communications.create_direct_channel(
            user1.identity_id,
            org.id,
            user2.identity_id,
        )

        with pytest.raises(ConflictError):
            communications.create_direct_channel(
                user1.identity_id,
                org.id,
                user2.identity_id,
            )

        with pytest.raises(ConflictError):
            communications.create_direct_channel(
                user2.identity_id,
                org.id,
                user1.identity_id,
            )

        row = db.execute(
            """
            SELECT count(*) AS count
            FROM channels
            WHERE organisation_id=?
              AND channel_type='DIRECT'
            """,
            (str(org.id),),
        ).fetchone()

        assert row["count"] == 1

        assert communications.get_channel(
            first["id"],
            user1.identity_id,
        )["direct_key"] == communications._direct_key(
            user1.identity_id,
            user2.identity_id,
        )

    finally:
        db.close()


def test_direct_channel_rejects_self_and_cross_tenant_target(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org1, user1, user2 = setup_company(core)

        with pytest.raises(ValidationError):
            communications.create_direct_channel(
                user1.identity_id,
                org1.id,
                user1.identity_id,
            )

        org2 = core.create_organisation("C2", "Other Company")
        user3 = core.create_user(
            "u3",
            "User 3",
            "Correct-Horse-Battery",
        )
        core.add_membership(user3.identity_id, org2.id)

        with pytest.raises(AuthorizationError):
            communications.create_direct_channel(
                user1.identity_id,
                org1.id,
                user3.identity_id,
            )

    finally:
        db.close()


def test_direct_channel_permission_enforcement(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org = core.create_organisation("C1", "Company")
        user1 = core.create_user(
            "u1",
            "User 1",
            "Correct-Horse-Battery",
        )
        user2 = core.create_user(
            "u2",
            "User 2",
            "Correct-Horse-Battery",
        )

        membership1 = core.add_membership(
            user1.identity_id,
            org.id,
        )
        core.add_membership(
            user2.identity_id,
            org.id,
        )

        role = core.create_role(
            org.id,
            "direct_limited_role",
            "Direct Limited Role",
        )
        core.assign_role(membership1.id, role.id)

        communications = core.communications_service

        with pytest.raises(AuthorizationError):
            communications.create_direct_channel(
                user1.identity_id,
                org.id,
                user2.identity_id,
            )

        permission = core.get_permission_by_code(
            "communications.channel.create"
        )
        core.grant_permission(role.id, permission.id)

        channel = communications.create_direct_channel(
            user1.identity_id,
            org.id,
            user2.identity_id,
        )

        assert channel["channel_type"] == "DIRECT"

    finally:
        db.close()


def test_direct_channel_creation_creates_audit_event(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org, user1, user2 = setup_company(core)
        communications = core.communications_service

        channel = communications.create_direct_channel(
            user1.identity_id,
            org.id,
            user2.identity_id,
        )

        events = core.list_audit_events(
            organisation_id=org.id,
            limit=100,
        )

        matching = [
            event
            for event in events
            if event.action == "DIRECT_CHANNEL_CREATED"
        ]

        assert len(matching) == 1
        assert matching[0].target_type == "CHANNEL"
        assert str(matching[0].target_id) == channel["id"]

    finally:
        db.close()


def test_direct_channel_cannot_cross_tenant_via_channel_access(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org1, user1, user2 = setup_company(core)

        channel = communications.create_direct_channel(
            user1.identity_id,
            org1.id,
            user2.identity_id,
        )

        org2 = core.create_organisation("C2", "Other Company")
        user3 = core.create_user(
            "u3",
            "User 3",
            "Correct-Horse-Battery",
        )
        core.add_membership(user3.identity_id, org2.id)

        with pytest.raises(AuthorizationError):
            communications.get_channel(
                channel["id"],
                user3.identity_id,
            )

    finally:
        db.close()
def test_group_channel_creation_and_membership(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        user3 = core.create_user(
            "u3",
            "User 3",
            "Correct-Horse-Battery",
        )
        core.add_membership(user3.identity_id, org.id)

        channel = communications.create_group_channel(
            user1.identity_id,
            org.id,
            "Project Team",
            [user2.identity_id, user3.identity_id],
        )

        assert channel["channel_type"] == "GROUP"
        assert channel["visibility"] == "PRIVATE"
        assert channel["direct_key"] is None

        members = db.execute(
            """
            SELECT identity_id
            FROM channel_members
            WHERE channel_id=?
              AND status='ACTIVE'
            ORDER BY identity_id
            """,
            (channel["id"],),
        ).fetchall()

        assert {row["identity_id"] for row in members} == {
            str(user1.identity_id),
            str(user2.identity_id),
            str(user3.identity_id),
        }
        assert len(members) == 3

        assert communications.get_channel(
            channel["id"],
            user2.identity_id,
        )["id"] == channel["id"]

        assert communications.get_channel(
            channel["id"],
            user3.identity_id,
        )["id"] == channel["id"]

    finally:
        db.close()


def test_group_channel_rejects_duplicate_members(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        with pytest.raises(ValidationError):
            communications.create_group_channel(
                user1.identity_id,
                org.id,
                "Duplicate Members",
                [user2.identity_id, user2.identity_id],
            )

        row = db.execute(
            """
            SELECT count(*) AS count
            FROM channels
            WHERE organisation_id=?
              AND channel_type='GROUP'
            """,
            (str(org.id),),
        ).fetchone()

        assert row["count"] == 0

    finally:
        db.close()


def test_group_channel_rejects_cross_tenant_members(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org1, user1, user2 = setup_company(core)

        org2 = core.create_organisation(
            "C2",
            "Other Company",
        )
        user3 = core.create_user(
            "u3",
            "User 3",
            "Correct-Horse-Battery",
        )
        core.add_membership(
            user3.identity_id,
            org2.id,
        )

        with pytest.raises(AuthorizationError):
            communications.create_group_channel(
                user1.identity_id,
                org1.id,
                "Cross Tenant Group",
                [user2.identity_id, user3.identity_id],
            )

        row = db.execute(
            """
            SELECT count(*) AS count
            FROM channels
            WHERE organisation_id=?
              AND channel_type='GROUP'
            """,
            (str(org1.id),),
        ).fetchone()

        assert row["count"] == 0

    finally:
        db.close()


def test_group_channel_duplicate_name_is_rejected(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org, user1, user2 = setup_company(core)

        communications.create_group_channel(
            user1.identity_id,
            org.id,
            "Engineering",
            [user2.identity_id],
        )

        with pytest.raises(ConflictError):
            communications.create_group_channel(
                user1.identity_id,
                org.id,
                "Engineering",
                [user2.identity_id],
            )

    finally:
        db.close()


def test_group_channel_permission_enforcement(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org = core.create_organisation(
            "C1",
            "Company",
        )

        user1 = core.create_user(
            "u1",
            "User 1",
            "Correct-Horse-Battery",
        )
        user2 = core.create_user(
            "u2",
            "User 2",
            "Correct-Horse-Battery",
        )

        membership1 = core.add_membership(
            user1.identity_id,
            org.id,
        )
        core.add_membership(
            user2.identity_id,
            org.id,
        )

        role = core.create_role(
            org.id,
            "group_limited_role",
            "Group Limited Role",
        )
        core.assign_role(
            membership1.id,
            role.id,
        )

        communications = core.communications_service

        with pytest.raises(AuthorizationError):
            communications.create_group_channel(
                user1.identity_id,
                org.id,
                "Engineering",
                [user2.identity_id],
            )

        permission = core.get_permission_by_code(
            "communications.channel.create"
        )
        core.grant_permission(
            role.id,
            permission.id,
        )

        channel = communications.create_group_channel(
            user1.identity_id,
            org.id,
            "Engineering",
            [user2.identity_id],
        )

        assert channel["channel_type"] == "GROUP"

    finally:
        db.close()


def test_group_channel_creation_creates_audit_event(tmp_path):
    db, core = make_service(tmp_path)

    try:
        org, user1, user2 = setup_company(core)
        communications = core.communications_service

        channel = communications.create_group_channel(
            user1.identity_id,
            org.id,
            "Audit Group",
            [user2.identity_id],
        )

        events = core.list_audit_events(
            organisation_id=org.id,
            limit=100,
        )

        matching = [
            event
            for event in events
            if event.action == "GROUP_CHANNEL_CREATED"
        ]

        assert len(matching) == 1
        assert matching[0].target_type == "CHANNEL"
        assert str(matching[0].target_id) == channel["id"]

    finally:
        db.close()


def test_group_channel_is_tenant_isolated(tmp_path):
    db, core = make_service(tmp_path)

    try:
        communications = core.communications_service
        org1, user1, user2 = setup_company(core)

        channel = communications.create_group_channel(
            user1.identity_id,
            org1.id,
            "Private Group",
            [user2.identity_id],
        )

        org2 = core.create_organisation(
            "C2",
            "Other Company",
        )
        user3 = core.create_user(
            "u3",
            "User 3",
            "Correct-Horse-Battery",
        )
        core.add_membership(
            user3.identity_id,
            org2.id,
        )

        with pytest.raises(AuthorizationError):
            communications.get_channel(
                channel["id"],
                user3.identity_id,
            )

    finally:
        db.close()
