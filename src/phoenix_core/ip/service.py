from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class IPOwnershipService:
    """Persistence and invariant layer for Phoenix IP ownership."""

    GLOBAL_OWNER_TYPES = {
        "FOUNDER",
        "LEGAL_ENTITY",
        "THIRD_PARTY",
        "OPEN_SOURCE",
    }

    COMPANY_OWNER_TYPE = "COMPANY"

    ASSET_TYPES = {
        "SOFTWARE",
        "ARCHITECTURE",
        "DATABASE",
        "ALGORITHM",
        "DESIGN",
        "DOCUMENTATION",
        "BRAND",
        "TRADEMARK",
        "INVENTION",
        "TRADE_SECRET",
        "CUSTOMER_CONTENT",
        "CUSTOMER_DATA",
        "THIRD_PARTY",
    }

    CONFIDENTIALITY_CLASSES = {
        "PUBLIC",
        "INTERNAL",
        "CONFIDENTIAL",
        "RESTRICTED",
        "TRADE_SECRET",
    }

    LICENCE_TYPES = {
        "PROPRIETARY",
        "OPEN_SOURCE",
        "COMMERCIAL",
        "CUSTOMER",
        "THIRD_PARTY",
    }

    ASSIGNMENT_TYPES = {
        "IP_ASSIGNMENT",
        "WORK_PRODUCT_ASSIGNMENT",
        "LICENCE",
        "CONFIDENTIALITY",
    }

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _id() -> str:
        return str(uuid4())

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _uuid(value: UUID | str | None) -> str | None:
        return None if value is None else str(value)

    def _require_owner(self, owner_id: UUID | str):
        row = self.db.execute(
            "SELECT * FROM ip_owners WHERE id=?",
            (self._uuid(owner_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("IP owner not found.")

        return row

    def _require_asset(self, asset_id: UUID | str):
        row = self.db.execute(
            """
            SELECT
                a.*,
                o.owner_type,
                o.organisation_id
            FROM ip_assets a
            JOIN ip_owners o ON o.id = a.owner_id
            WHERE a.id=?
            """,
            (self._uuid(asset_id),),
        ).fetchone()

        if not row:
            raise NotFoundError("IP asset not found.")

        return row

    @staticmethod
    def _assert_owner_tenant(owner, organisation_id):
        owner_type = owner["owner_type"]
        owner_org = owner["organisation_id"]

        if owner_type == "COMPANY":
            if not owner_org:
                raise ValidationError(
                    "Company IP owners must have an organisation."
                )

            if organisation_id is None:
                raise AuthorizationError(
                    "Organisation context required for company-owned IP."
                )

            if str(owner_org) != str(organisation_id):
                raise AuthorizationError(
                    "IP owner does not belong to this organisation."
                )
            return

        if owner_org is not None:
            raise ValidationError(
                "Global IP owners cannot be assigned to an organisation."
            )

    # ------------------------------------------------------------------
    # Owners
    # ------------------------------------------------------------------

    def create_owner(
        self,
        *,
        owner_type: str,
        name: str,
        description: str | None = None,
        organisation_id: UUID | str | None = None,
    ) -> dict:
        owner_type = owner_type.upper().strip()

        if owner_type not in self.GLOBAL_OWNER_TYPES | {self.COMPANY_OWNER_TYPE}:
            raise ValidationError("Invalid IP owner type.")

        if not name or not name.strip():
            raise ValidationError("IP owner name is required.")

        if owner_type == self.COMPANY_OWNER_TYPE:
            if organisation_id is None:
                raise ValidationError(
                    "Company IP owners require an organisation."
                )
        elif organisation_id is not None:
            raise ValidationError(
                "Global IP owners cannot have an organisation."
            )

        owner_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_owners (
                id, owner_type, name, description, organisation_id,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            """,
            (
                owner_id,
                owner_type,
                name.strip(),
                description,
                self._uuid(organisation_id),
                now,
                now,
            ),
        )
        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_owners WHERE id=?",
                (owner_id,),
            ).fetchone()
        )

    def get_owner(
        self,
        owner_id: UUID | str,
        *,
        organisation_id: UUID | str | None = None,
    ) -> dict:
        row = self._require_owner(owner_id)
        self._assert_owner_tenant(row, organisation_id)
        return dict(row)

    def list_owners(
        self,
        *,
        organisation_id: UUID | str | None = None,
        owner_type: str | None = None,
    ) -> list[dict]:
        params = []

        sql = """
            SELECT *
            FROM ip_owners
            WHERE status='ACTIVE'
        """

        if organisation_id is not None:
            sql += """
                AND (
                    organisation_id=?
                    OR organisation_id IS NULL
                )
            """
            params.append(self._uuid(organisation_id))
        else:
            sql += " AND organisation_id IS NULL"

        if owner_type:
            sql += " AND owner_type=?"
            params.append(owner_type.upper().strip())

        sql += " ORDER BY name"

        return [
            dict(row)
            for row in self.db.execute(sql, tuple(params)).fetchall()
        ]

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    def create_asset(
        self,
        *,
        owner_id: UUID | str,
        asset_code: str,
        name: str,
        asset_type: str,
        confidentiality_class: str = "INTERNAL",
        description: str | None = None,
        organisation_id: UUID | str | None = None,
    ) -> dict:
        owner = self._require_owner(owner_id)
        self._assert_owner_tenant(owner, organisation_id)

        asset_type = asset_type.upper().strip()
        confidentiality_class = confidentiality_class.upper().strip()

        if asset_type not in self.ASSET_TYPES:
            raise ValidationError("Invalid IP asset type.")

        if confidentiality_class not in self.CONFIDENTIALITY_CLASSES:
            raise ValidationError("Invalid confidentiality class.")

        if not asset_code or not asset_code.strip():
            raise ValidationError("IP asset code is required.")

        if not name or not name.strip():
            raise ValidationError("IP asset name is required.")

        if self.db.execute(
            "SELECT id FROM ip_assets WHERE asset_code=?",
            (asset_code.strip(),),
        ).fetchone():
            raise ConflictError("IP asset code already exists.")

        asset_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_assets (
                id, owner_id, asset_code, name, description,
                asset_type, confidentiality_class, status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            """,
            (
                asset_id,
                self._uuid(owner_id),
                asset_code.strip(),
                name.strip(),
                description,
                asset_type,
                confidentiality_class,
                now,
                now,
            ),
        )

        self.db.execute(
            """
            INSERT INTO ip_ownership_events (
                id, asset_id, previous_owner_id, new_owner_id,
                event_type, reason, effective_at, created_at
            )
            VALUES (?, ?, NULL, ?, 'CREATED', ?, ?, ?)
            """,
            (
                self._id(),
                asset_id,
                self._uuid(owner_id),
                "Initial IP asset ownership",
                now,
                now,
            ),
        )

        self.db.commit()

        return dict(self._require_asset(asset_id))

    def get_asset(
        self,
        asset_id: UUID | str,
        *,
        organisation_id: UUID | str | None = None,
    ) -> dict:
        row = self._require_asset(asset_id)
        self._assert_owner_tenant(row, organisation_id)
        return dict(row)

    def list_assets(
        self,
        *,
        organisation_id: UUID | str | None = None,
        owner_id: UUID | str | None = None,
        asset_type: str | None = None,
    ) -> list[dict]:
        params = []

        sql = """
            SELECT
                a.*,
                o.owner_type,
                o.name AS owner_name,
                o.organisation_id
            FROM ip_assets a
            JOIN ip_owners o ON o.id=a.owner_id
            WHERE a.status != 'RETIRED'
        """

        if organisation_id is not None:
            sql += """
                AND (
                    o.organisation_id=?
                    OR o.organisation_id IS NULL
                )
            """
            params.append(self._uuid(organisation_id))
        else:
            sql += " AND o.organisation_id IS NULL"

        if owner_id is not None:
            sql += " AND a.owner_id=?"
            params.append(self._uuid(owner_id))

        if asset_type:
            sql += " AND a.asset_type=?"
            params.append(asset_type.upper().strip())

        sql += " ORDER BY a.name"

        return [
            dict(row)
            for row in self.db.execute(sql, tuple(params)).fetchall()
        ]

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------

    def record_ownership_transfer(
        self,
        asset_id: UUID | str,
        *,
        new_owner_id: UUID | str,
        organisation_id: UUID | str | None = None,
        reason: str | None = None,
        document_id: UUID | str | None = None,
        document_version_id: UUID | str | None = None,
        created_by_identity_id: UUID | str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        current_owner = self._require_owner(asset["owner_id"])
        new_owner = self._require_owner(new_owner_id)

        self._assert_owner_tenant(current_owner, organisation_id)
        self._assert_owner_tenant(new_owner, organisation_id)

        if current_owner["id"] == new_owner["id"]:
            raise ValidationError(
                "New owner must differ from the current owner."
            )

        now = self._now()

        self.db.execute(
            """
            UPDATE ip_assets
            SET owner_id=?, updated_at=?
            WHERE id=?
            """,
            (
                self._uuid(new_owner_id),
                now,
                self._uuid(asset_id),
            ),
        )

        event_id = self._id()

        self.db.execute(
            """
            INSERT INTO ip_ownership_events (
                id, asset_id, previous_owner_id, new_owner_id,
                event_type, reason, document_id, document_version_id,
                effective_at, created_at, created_by_identity_id
            )
            VALUES (?, ?, ?, ?, 'TRANSFERRED', ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                self._uuid(asset_id),
                current_owner["id"],
                self._uuid(new_owner_id),
                reason,
                self._uuid(document_id),
                self._uuid(document_version_id),
                now,
                now,
                self._uuid(created_by_identity_id),
            ),
        )

        self.db.commit()

        return {
            "event_id": event_id,
            "asset": dict(self._require_asset(asset_id)),
        }

    # ------------------------------------------------------------------
    # Licences
    # ------------------------------------------------------------------

    def create_asset_version(
        self,
        asset_id: UUID | str,
        *,
        version_label: str,
        organisation_id: UUID | str | None = None,
        description: str | None = None,
        document_id: UUID | str | None = None,
        document_version_id: UUID | str | None = None,
        checksum: str | None = None,
        effective_from: str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        self._assert_owner_tenant(asset, organisation_id)

        version_label = version_label.strip()

        if not version_label:
            raise ValidationError(
                "Asset version label is required."
            )

        if document_id is not None or document_version_id is not None:
            if document_id is None or document_version_id is None:
                raise ValidationError(
                    "document_id and document_version_id must be supplied together."
                )

            document = self.db.execute(
                "SELECT id FROM documents WHERE id=?",
                (self._uuid(document_id),),
            ).fetchone()

            if not document:
                raise ValidationError("Document not found.")

            document_version = self.db.execute(
                """
                SELECT id, document_id
                FROM document_versions
                WHERE id=?
                """,
                (self._uuid(document_version_id),),
            ).fetchone()

            if not document_version:
                raise ValidationError("Document version not found.")

            if document_version["document_id"] != self._uuid(document_id):
                raise ValidationError(
                    "Document version does not belong to the supplied document."
                )

        existing = self.db.execute(
            """
            SELECT id
            FROM ip_asset_versions
            WHERE asset_id=? AND version_label=?
            """,
            (
                self._uuid(asset_id),
                version_label,
            ),
        ).fetchone()

        if existing:
            raise ValidationError(
                "An IP asset version with this label already exists."
            )

        version_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_asset_versions (
                id,
                asset_id,
                version_label,
                description,
                document_id,
                document_version_id,
                checksum,
                effective_from,
                retired_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                version_id,
                self._uuid(asset_id),
                version_label,
                description,
                self._uuid(document_id),
                self._uuid(document_version_id),
                checksum,
                effective_from,
                now,
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_asset_versions WHERE id=?",
                (version_id,),
            ).fetchone()
        )

    def get_asset_version(
        self,
        version_id: UUID | str,
        *,
        organisation_id: UUID | str | None = None,
    ) -> dict:
        row = self.db.execute(
            """
            SELECT
                v.*,
                a.owner_id
            FROM ip_asset_versions v
            JOIN ip_assets a
                ON a.id=v.asset_id
            WHERE v.id=?
            """,
            (self._uuid(version_id),),
        ).fetchone()

        if not row:
            raise ValidationError("IP asset version not found.")

        asset = self._require_asset(row["asset_id"])
        self._assert_owner_tenant(asset, organisation_id)

        return dict(row)

    def list_asset_versions(
        self,
        asset_id: UUID | str,
        *,
        organisation_id: UUID | str | None = None,
    ) -> list[dict]:
        asset = self._require_asset(asset_id)
        self._assert_owner_tenant(asset, organisation_id)

        rows = self.db.execute(
            """
            SELECT *
            FROM ip_asset_versions
            WHERE asset_id=?
            ORDER BY created_at, version_label
            """,
            (self._uuid(asset_id),),
        ).fetchall()

        return [dict(row) for row in rows]

    def retire_asset_version(
        self,
        version_id: UUID | str,
        *,
        organisation_id: UUID | str | None = None,
        retired_at: str | None = None,
    ) -> dict:
        row = self.db.execute(
            """
            SELECT asset_id
            FROM ip_asset_versions
            WHERE id=?
            """,
            (self._uuid(version_id),),
        ).fetchone()

        if not row:
            raise ValidationError("IP asset version not found.")

        asset = self._require_asset(row["asset_id"])
        self._assert_owner_tenant(asset, organisation_id)

        value = retired_at or self._now()

        self.db.execute(
            """
            UPDATE ip_asset_versions
            SET retired_at=?
            WHERE id=?
            """,
            (
                value,
                self._uuid(version_id),
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_asset_versions WHERE id=?",
                (self._uuid(version_id),),
            ).fetchone()
        )

    def create_licence(
        self,
        asset_id: UUID | str,
        *,
        licence_type: str,
        organisation_id: UUID | str | None = None,
        licence_name: str | None = None,
        licence_version: str | None = None,
        licensor: str | None = None,
        licensee: str | None = None,
        permitted_use: str | None = None,
        restrictions: str | None = None,
        source_url: str | None = None,
        document_id: UUID | str | None = None,
        document_version_id: UUID | str | None = None,
        effective_from: str | None = None,
        expires_at: str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        self._assert_owner_tenant(asset, organisation_id)

        licence_type = licence_type.upper().strip()

        if licence_type not in self.LICENCE_TYPES:
            raise ValidationError("Invalid IP licence type.")

        licence_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_licences (
                id, asset_id, licence_type, licence_name,
                licence_version, licensor, licensee, permitted_use,
                restrictions, source_url, document_id,
                document_version_id, effective_from, expires_at,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'ACTIVE', ?, ?)
            """,
            (
                licence_id,
                self._uuid(asset_id),
                licence_type,
                licence_name,
                licence_version,
                licensor,
                licensee,
                permitted_use,
                restrictions,
                source_url,
                self._uuid(document_id),
                self._uuid(document_version_id),
                effective_from,
                expires_at,
                now,
                now,
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_licences WHERE id=?",
                (licence_id,),
            ).fetchone()
        )

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------

    def record_assignment(
        self,
        asset_id: UUID | str,
        *,
        assignee_owner_id: UUID | str,
        document_id: UUID | str,
        document_version_id: UUID | str,
        assignment_type: str,
        organisation_id: UUID | str | None = None,
        assignor_owner_id: UUID | str | None = None,
        effective_at: str | None = None,
        expires_at: str | None = None,
        notes: str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        assignee = self._require_owner(assignee_owner_id)

        self._assert_owner_tenant(asset, organisation_id)
        self._assert_owner_tenant(assignee, organisation_id)

        if assignor_owner_id is not None:
            assignor = self._require_owner(assignor_owner_id)
            self._assert_owner_tenant(assignor, organisation_id)

        assignment_type = assignment_type.upper().strip()

        if assignment_type not in self.ASSIGNMENT_TYPES:
            raise ValidationError("Invalid IP assignment type.")

        if not document_id or not document_version_id:
            raise ValidationError(
                "Assignment document and document version are required."
            )

        assignment_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_contractual_assignments (
                id, asset_id, assignor_owner_id, assignee_owner_id,
                assignment_type, document_id, document_version_id,
                effective_at, expires_at, status, notes,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
            """,
            (
                assignment_id,
                self._uuid(asset_id),
                self._uuid(assignor_owner_id),
                self._uuid(assignee_owner_id),
                assignment_type,
                self._uuid(document_id),
                self._uuid(document_version_id),
                effective_at or now,
                expires_at,
                notes,
                now,
                now,
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_contractual_assignments WHERE id=?",
                (assignment_id,),
            ).fetchone()
        )

    # ------------------------------------------------------------------
    # Confidentiality
    # ------------------------------------------------------------------

    def create_confidentiality_record(
        self,
        asset_id: UUID | str,
        *,
        owner_id: UUID | str,
        party_name: str,
        confidentiality_type: str,
        document_id: UUID | str,
        document_version_id: UUID | str,
        effective_at: str,
        organisation_id: UUID | str | None = None,
        expires_at: str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        owner = self._require_owner(owner_id)

        self._assert_owner_tenant(asset, organisation_id)
        self._assert_owner_tenant(owner, organisation_id)

        confidentiality_type = confidentiality_type.upper().strip()

        if confidentiality_type not in {
            "NDA",
            "CONTRACTUAL",
            "EMPLOYEE",
            "CONTRACTOR",
            "CUSTOMER",
        }:
            raise ValidationError("Invalid confidentiality type.")

        if not party_name or not party_name.strip():
            raise ValidationError("Confidentiality party name is required.")

        record_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_confidentiality_records (
                id, asset_id, owner_id, party_name,
                confidentiality_type, document_id,
                document_version_id, effective_at, expires_at,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            """,
            (
                record_id,
                self._uuid(asset_id),
                self._uuid(owner_id),
                party_name.strip(),
                confidentiality_type,
                self._uuid(document_id),
                self._uuid(document_version_id),
                effective_at,
                expires_at,
                now,
                now,
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_confidentiality_records WHERE id=?",
                (record_id,),
            ).fetchone()
        )

    # ------------------------------------------------------------------
    # Third-party components
    # ------------------------------------------------------------------

    def register_third_party_component(
        self,
        asset_id: UUID | str,
        *,
        component_name: str,
        organisation_id: UUID | str | None = None,
        component_version: str | None = None,
        supplier: str | None = None,
        licence_id: UUID | str | None = None,
        source_url: str | None = None,
        usage_notes: str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        self._assert_owner_tenant(asset, organisation_id)

        if not component_name or not component_name.strip():
            raise ValidationError(
                "Third-party component name is required."
            )

        if licence_id is not None:
            licence = self.db.execute(
                "SELECT * FROM ip_licences WHERE id=?",
                (self._uuid(licence_id),),
            ).fetchone()

            if not licence:
                raise NotFoundError("IP licence not found.")

            if licence["asset_id"] != self._uuid(asset_id):
                raise AuthorizationError(
                    "Licence does not belong to this IP asset."
                )

        component_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_third_party_components (
                id, asset_id, component_name, component_version,
                supplier, licence_id, source_url, usage_notes,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                component_id,
                self._uuid(asset_id),
                component_name.strip(),
                component_version,
                supplier,
                self._uuid(licence_id),
                source_url,
                usage_notes,
                now,
                now,
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_third_party_components WHERE id=?",
                (component_id,),
            ).fetchone()
        )

    # ------------------------------------------------------------------
    # Documents
    # ------------------------------------------------------------------

    def add_asset_document(
        self,
        asset_id: UUID | str,
        *,
        document_id: UUID | str,
        document_version_id: UUID | str,
        document_role: str,
        organisation_id: UUID | str | None = None,
    ) -> dict:
        asset = self._require_asset(asset_id)
        self._assert_owner_tenant(asset, organisation_id)

        document_role = document_role.upper().strip()

        if document_role not in {
            "OWNERSHIP",
            "ASSIGNMENT",
            "LICENCE",
            "NDA",
            "REGISTRATION",
            "EVIDENCE",
            "OTHER",
        }:
            raise ValidationError("Invalid IP document role.")

        document = self.db.execute(
            "SELECT id FROM documents WHERE id=?",
            (self._uuid(document_id),),
        ).fetchone()

        if not document:
            raise NotFoundError("Document not found.")

        version = self.db.execute(
            """
            SELECT id, document_id
            FROM document_versions
            WHERE id=?
            """,
            (self._uuid(document_version_id),),
        ).fetchone()

        if not version:
            raise NotFoundError("Document version not found.")

        if version["document_id"] != self._uuid(document_id):
            raise ValidationError(
                "Document version does not belong to the document."
            )

        existing = self.db.execute(
            """
            SELECT id
            FROM ip_asset_documents
            WHERE asset_id=?
              AND document_id=?
              AND document_version_id=?
              AND document_role=?
            """,
            (
                self._uuid(asset_id),
                self._uuid(document_id),
                self._uuid(document_version_id),
                document_role,
            ),
        ).fetchone()

        if existing:
            raise ConflictError(
                "This IP document association already exists."
            )

        association_id = self._id()
        now = self._now()

        self.db.execute(
            """
            INSERT INTO ip_asset_documents (
                id, asset_id, document_id, document_version_id,
                document_role, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                association_id,
                self._uuid(asset_id),
                self._uuid(document_id),
                self._uuid(document_version_id),
                document_role,
                now,
            ),
        )

        self.db.commit()

        return dict(
            self.db.execute(
                "SELECT * FROM ip_asset_documents WHERE id=?",
                (association_id,),
            ).fetchone()
        )

    def list_asset_documents(
        self,
        asset_id: UUID | str,
        *,
        organisation_id: UUID | str | None = None,
    ) -> list[dict]:
        asset = self._require_asset(asset_id)
        self._assert_owner_tenant(asset, organisation_id)

        rows = self.db.execute(
            """
            SELECT *
            FROM ip_asset_documents
            WHERE asset_id=?
            ORDER BY created_at
            """,
            (self._uuid(asset_id),),
        ).fetchall()

        return [dict(row) for row in rows]
