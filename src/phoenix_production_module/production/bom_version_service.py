from uuid import UUID

from phoenix_core.errors import ConflictError, NotFoundError, ValidationError


class BOMVersionService:
    def __init__(self, db):
        self.db = db

    def create_version(
        self,
        *,
        organisation_id: UUID,
        bom_id: UUID,
        version_number: int,
        spc_definition_id: UUID | None = None,
    ):
        row = self.db.execute(
            """
            SELECT id
            FROM production_boms
            WHERE id=? AND organisation_id=?
            """,
            (str(bom_id), str(organisation_id)),
        ).fetchone()

        if row is None:
            raise NotFoundError("BOM not found")

        if version_number < 1:
            raise ValidationError("Version number must be >= 1")

        if spc_definition_id is not None:
            spc = self.db.execute(
                """
                SELECT id, status
                FROM production_spc_definitions
                WHERE id=? AND organisation_id=?
                """,
                (str(spc_definition_id), str(organisation_id)),
            ).fetchone()

            if spc is None:
                raise NotFoundError("SPC definition not found")

            if spc["status"] != "ACTIVE":
                raise ValidationError(
                    "BOM version can only use an ACTIVE SPC definition"
                )

        from .bom import BOMVersion

        version = BOMVersion.create(
            bom_id=bom_id,
            version_number=version_number,
            spc_definition_id=spc_definition_id,
        )

        try:
            self.db.execute(
                """
                INSERT INTO production_bom_versions(
                    id,
                    bom_id,
                    version_number,
                    status,
                    created_at,
                    spc_definition_id
                )
                VALUES (?,?,?,?,?,?)
                """,
                (
                    str(version.id),
                    str(version.bom_id),
                    version.version_number,
                    version.status,
                    version.created_at.isoformat(),
                    str(spc_definition_id) if spc_definition_id else None,
                ),
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if (
                "UNIQUE constraint failed: "
                "production_bom_versions.bom_id, "
                "production_bom_versions.version_number"
            ) in str(exc):
                raise ConflictError(
                    "BOM version number already exists"
                ) from exc
            raise

        return self.get_version(
            organisation_id=organisation_id,
            version_id=version.id,
        )

    def publish_version(
        self,
        *,
        organisation_id: UUID,
        version_id: UUID,
        published_by: UUID | None = None,
    ):
        current = self.get_version(
            organisation_id=organisation_id,
            version_id=version_id,
        )

        published = current.publish()

        try:
            self.db.execute(
                """
                UPDATE production_bom_versions
                SET status='PUBLISHED',
                    published_at=?,
                    published_by=?
                WHERE id=?
                  AND bom_id IN (
                      SELECT id
                      FROM production_boms
                      WHERE organisation_id=?
                  )
                """,
                (
                    published.published_at.isoformat(),
                    str(published_by) if published_by else None,
                    str(version_id),
                    str(organisation_id),
                ),
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self.get_version(
            organisation_id=organisation_id,
            version_id=version_id,
        )
    def get_version(self, *, organisation_id: UUID, version_id: UUID):
        row = self.db.execute(
            """
            SELECT
                v.id,
                v.bom_id,
                v.version_number,
                v.status,
                v.created_at,
                v.published_at,
                v.spc_definition_id
            FROM production_bom_versions v
            JOIN production_boms b
              ON b.id = v.bom_id
            WHERE v.id=?
              AND b.organisation_id=?
            """,
            (str(version_id), str(organisation_id)),
        ).fetchone()

        if row is None:
            raise NotFoundError("BOM version not found")

        from .bom import BOMVersion

        result = BOMVersion(
            id=UUID(row["id"]),
            bom_id=UUID(row["bom_id"]),
            version_number=row["version_number"],
            status=row["status"],
            created_at=__import__("datetime").datetime.fromisoformat(
                row["created_at"]
            ),
            published_at=(
                __import__("datetime").datetime.fromisoformat(
                    row["published_at"]
                )
                if row["published_at"]
                else None
            ),
            spc_definition_id=(UUID(row["spc_definition_id"]) if row["spc_definition_id"] else None),
        )

        return result




