"""Customer Master import application workflow."""

import json
from pathlib import Path
from uuid import uuid4

from phoenix_core.api.contracts import ApiResponse
from phoenix_core.errors import AuthorizationError, ValidationError

from phoenix_company.application.customer_import_parser import (
    parse_customer_master_file,
)


class CustomerImportApplicationService:
    """Company Platform workflow for Customer Master imports."""

    def __init__(self, core_api):
        self.core_api = core_api
        self.db = core_api.db

    def create_import_job(
        self,
        context,
        *,
        source_filename: str,
        source_system: str,
        file_hash: str,
        total_rows: int,
    ) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.data.import",
        )

        job_id = str(uuid4())

        self.db.execute(
            """
            INSERT INTO import_jobs (
                id,
                organisation_id,
                import_type,
                source_filename,
                source_system,
                status,
                uploaded_by,
                uploaded_at,
                total_rows,
                valid_rows,
                invalid_rows,
                warning_rows,
                inserted_rows,
                updated_rows,
                unchanged_rows,
                file_hash,
                created_at,
                updated_at
            )
            VALUES (
                ?,
                ?,
                'CUSTOMER_MASTER',
                ?,
                ?,
                'UPLOADED',
                ?,
                CURRENT_TIMESTAMP,
                ?,
                0,
                0,
                0,
                0,
                0,
                0,
                ?,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """,
            (
                job_id,
                str(context.organisation_id),
                source_filename,
                source_system,
                str(context.identity_id),
                total_rows,
                file_hash,
            ),
        )

        self.db.commit()

        return ApiResponse(
            data={
                "id": job_id,
                "status": "UPLOADED",
                "total_rows": total_rows,
            },
            request_id=context.request_id,
        )

    def validate_import_job(
        self,
        context,
        job_id: str,
        *,
        file_path: str | Path,
    ) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.data.import",
        )

        job = self.db.execute(
            """
            SELECT
                id,
                organisation_id,
                status,
                total_rows
            FROM import_jobs
            WHERE id=?
            """,
            (job_id,),
        ).fetchone()

        if job is None:
            raise ValidationError(
                "Import job was not found."
            )

        if str(job["organisation_id"]) != str(
            context.organisation_id
        ):
            raise AuthorizationError(
                "Import job does not belong to the current organisation."
            )

        if job["status"] != "UPLOADED":
            raise ValidationError(
                f"Import job cannot be validated from status "
                f"'{job['status']}'."
            )

        try:
            result = parse_customer_master_file(
                file_path
            )

            self.db.execute(
                "DELETE FROM import_job_rows WHERE import_job_id=?",
                (job_id,),
            )

            warning_rows = sum(
                bool(row.validation_warnings)
                for row in result.rows
            )

            for row in result.rows:
                action = (
                    "REJECT"
                    if row.validation_status == "INVALID"
                    else None
                )

                raw_data = {
                    "values": row.values,
                    "display_name": row.display_name,
                }

                self.db.execute(
                    """
                    INSERT INTO import_job_rows (
                        id,
                        import_job_id,
                        row_number,
                        external_id,
                        warehouse_external_id,
                        raw_data_json,
                        validation_status,
                        validation_errors_json,
                        validation_warnings_json,
                        action
                    )
                    VALUES (
                        ?,
                        ?,
                        ?,
                        ?,
                        NULL,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )
                    """,
                    (
                        str(uuid4()),
                        job_id,
                        row.row_number,
                        row.external_id or None,
                        json.dumps(
                            raw_data,
                            default=str,
                        ),
                        row.validation_status,
                        json.dumps(
                            row.validation_errors
                        ),
                        json.dumps(
                            row.validation_warnings
                        ),
                        action,
                    ),
                )

            error_summary = None

            if result.invalid_rows:
                errors = [
                    {
                        "row_number": row.row_number,
                        "errors": row.validation_errors,
                    }
                    for row in result.rows
                    if row.validation_errors
                ]

                error_summary = json.dumps(
                    errors[:25]
                )

            self.db.execute(
                """
                UPDATE import_jobs
                SET
                    status='VALIDATED',
                    validated_at=CURRENT_TIMESTAMP,
                    total_rows=?,
                    valid_rows=?,
                    invalid_rows=?,
                    warning_rows=?,
                    error_summary=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    result.total_rows,
                    result.valid_rows,
                    result.invalid_rows,
                    warning_rows,
                    error_summary,
                    job_id,
                ),
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(
            data={
                "id": job_id,
                "status": "VALIDATED",
                "total_rows": result.total_rows,
                "valid_rows": result.valid_rows,
                "invalid_rows": result.invalid_rows,
                "warning_rows": warning_rows,
            },
            request_id=context.request_id,
        )

    def get_import_preview(
        self,
        context,
        job_id: str,
    ) -> ApiResponse:
        self.core_api.require_permission(
            context,
            "company.data.import",
        )

        job = self.db.execute(
            """
            SELECT
                id,
                organisation_id,
                status
            FROM import_jobs
            WHERE id=?
            """,
            (job_id,),
        ).fetchone()

        if job is None:
            raise ValidationError(
                "Import job was not found."
            )

        if str(job["organisation_id"]) != str(
            context.organisation_id
        ):
            raise AuthorizationError(
                "Import job does not belong to the current organisation."
            )

        if job["status"] != "VALIDATED":
            raise ValidationError(
                f"Import job cannot be previewed from status "
                f"'{job['status']}'."
            )

        rows = self.db.execute(
            """
            SELECT
                row_number,
                external_id,
                raw_data_json,
                validation_status,
                validation_errors_json,
                validation_warnings_json,
                action
            FROM import_job_rows
            WHERE import_job_id=?
            ORDER BY row_number
            LIMIT 25
            """,
            (job_id,),
        ).fetchall()

        preview = []

        for row in rows:
            raw_data = json.loads(
                row["raw_data_json"]
            )

            errors = json.loads(
                row["validation_errors_json"] or "[]"
            )

            warnings = json.loads(
                row["validation_warnings_json"] or "[]"
            )

            preview.append(
                {
                    "row_number": row["row_number"],
                    "external_id": row["external_id"],
                    "display_name": raw_data.get(
                        "display_name",
                        "",
                    ),
                    "validation_status": row[
                        "validation_status"
                    ],
                    "validation_errors": errors,
                    "validation_warnings": warnings,
                    "action": row["action"],
                }
            )

        return ApiResponse(
            data={
                "id": job_id,
                "status": job["status"],
                "rows": preview,
            },
            request_id=context.request_id,
        )

    def confirm_import(
        self,
        context,
        job_id: str,
    ) -> ApiResponse:
        """Confirm a validated Customer Master import atomically."""

        self.core_api.require_permission(
            context,
            "company.data.import",
        )

        try:
            self.db.execute("BEGIN IMMEDIATE")

            job = self.db.execute(
                """
                SELECT
                    id,
                    organisation_id,
                    source_system,
                    status,
                    total_rows,
                    valid_rows,
                    invalid_rows
                FROM import_jobs
                WHERE id=?
                """,
                (job_id,),
            ).fetchone()

            if job is None:
                raise ValidationError(
                    "Import job was not found."
                )

            if str(job["organisation_id"]) != str(
                context.organisation_id
            ):
                raise AuthorizationError(
                    "Import job does not belong to the current organisation."
                )

            if job["status"] != "VALIDATED":
                raise ValidationError(
                    f"Import job cannot be confirmed from status "
                    f"'{job['status']}'."
                )

            if int(job["invalid_rows"]) > 0:
                raise ValidationError(
                    "Import job contains invalid rows and cannot be confirmed."
                )

            rows = self.db.execute(
                """
                SELECT
                    id,
                    external_id,
                    raw_data_json,
                    validation_status,
                    action
                FROM import_job_rows
                WHERE import_job_id=?
                ORDER BY row_number
                """,
                (job_id,),
            ).fetchall()

            if not rows:
                raise ValidationError(
                    "Import job contains no rows to commit."
                )

            inserted_rows = 0
            updated_rows = 0
            unchanged_rows = 0

            organisation_id = str(
                context.organisation_id
            )
            source_system = str(
                job["source_system"]
            )

            for row in rows:
                if row["validation_status"] != "VALID":
                    raise ValidationError(
                        "Import job contains a non-valid row and "
                        "cannot be confirmed."
                    )

                external_id = (
                    str(row["external_id"]).strip()
                    if row["external_id"] is not None
                    else ""
                )

                if not external_id:
                    raise ValidationError(
                        "A valid import row is missing its external customer ID."
                    )

                raw_data = json.loads(
                    row["raw_data_json"]
                )

                display_name = str(
                    raw_data.get("display_name", "")
                ).strip()

                if not display_name:
                    raise ValidationError(
                        f'Customer "{external_id}" is missing its display name.'
                    )

                existing = self.db.execute(
                    """
                    SELECT
                        id,
                        display_name,
                        status
                    FROM customer_references
                    WHERE organisation_id=?
                      AND source_system=?
                      AND external_customer_id=?
                    """,
                    (
                        organisation_id,
                        source_system,
                        external_id,
                    ),
                ).fetchone()

                if existing is None:
                    self.db.execute(
                        """
                        INSERT INTO customer_references (
                            id,
                            organisation_id,
                            source_system,
                            external_customer_id,
                            display_name,
                            status,
                            source_record_url,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            'ACTIVE',
                            NULL,
                            CURRENT_TIMESTAMP,
                            CURRENT_TIMESTAMP
                        )
                        """,
                        (
                            str(uuid4()),
                            organisation_id,
                            source_system,
                            external_id,
                            display_name,
                        ),
                    )

                    inserted_rows += 1
                    continue

                if str(existing["display_name"]) == display_name:
                    unchanged_rows += 1
                    continue

                self.db.execute(
                    """
                    UPDATE customer_references
                    SET
                        display_name=?,
                        status='ACTIVE',
                        updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (
                        display_name,
                        existing["id"],
                    ),
                )

                updated_rows += 1

            self.db.execute(
                """
                UPDATE import_job_rows
                SET action='COMMIT'
                WHERE import_job_id=?
                  AND validation_status='VALID'
                """,
                (job_id,),
            )

            self.db.execute(
                """
                UPDATE import_jobs
                SET
                    status='COMPLETED',
                    confirmed_at=CURRENT_TIMESTAMP,
                    completed_at=CURRENT_TIMESTAMP,
                    inserted_rows=?,
                    updated_rows=?,
                    unchanged_rows=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (
                    inserted_rows,
                    updated_rows,
                    unchanged_rows,
                    job_id,
                ),
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(
            data={
                "id": job_id,
                "status": "COMPLETED",
                "inserted_rows": inserted_rows,
                "updated_rows": updated_rows,
                "unchanged_rows": unchanged_rows,
            },
            request_id=context.request_id,
        )