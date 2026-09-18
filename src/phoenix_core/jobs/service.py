"""Phoenix Core background-job service."""

import json
from datetime import datetime, timezone
from uuid import UUID
from typing import List

from phoenix_core.audit.domain import AuditEvent
from phoenix_core.audit.service import AuditService
from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobRequest
from phoenix_core.jobs.domain import Job


class JobService:
    """Application service for Core background-job persistence and lifecycle."""

    def __init__(
        self,
        db: SQLiteDatabase,
        audit_service: AuditService | None = None,
    ):
        self.db = db
        self.audit_service = audit_service

    def _audit_job(self, job: Job, action: str) -> None:
        """Record a Core audit event for a job lifecycle transition."""
        if self.audit_service is None:
            return

        self.audit_service.record(
            AuditEvent.create(
                organisation_id=job.organisation_id,
                identity_id=job.identity_id,
                action=action,
                target_type="JOB",
                target_id=job.id,
                request_id=job.request_id,
            )
        )

    def enqueue(
        self,
        request: JobRequest,
        max_attempts: int = 3,
    ) -> Job:
        if not request.request_id or not request.request_id.strip():
            raise ValidationError("request_id is required.")

        if not request.job_type or not request.job_type.strip():
            raise ValidationError("job_type is required.")

        if max_attempts < 1:
            raise ValidationError("max_attempts must be at least 1.")

        if request.idempotency_key is not None and not request.idempotency_key.strip():
            raise ValidationError("idempotency_key cannot be empty.")

        if request.idempotency_key and request.organisation_id is None:
            raise ValidationError(
                "organisation_id is required when idempotency_key is supplied."
            )

        if request.idempotency_key:
            existing = self.db.execute(
                """
                SELECT id
                FROM jobs
                WHERE organisation_id = ?
                  AND idempotency_key = ?
                """,
                (
                    str(request.organisation_id),
                    request.idempotency_key,
                ),
            ).fetchone()

            if existing:
                return self.get(UUID(existing["id"]))

        job = Job.create(
            request_id=request.request_id,
            job_type=request.job_type,
            organisation_id=request.organisation_id,
            identity_id=request.identity_id,
            payload=request.payload,
            scheduled_at=request.scheduled_at,
            idempotency_key=request.idempotency_key,
            max_attempts=max_attempts,
        )

        payload = (
            json.dumps(request.payload)
            if request.payload is not None
            else None
        )

        try:
            self.db.execute(
                """
                INSERT INTO jobs (
                    id,
                    request_id,
                    job_type,
                    organisation_id,
                    identity_id,
                    payload,
                    status,
                    scheduled_at,
                    created_at,
                    started_at,
                    completed_at,
                    failed_at,
                    attempt_count,
                    max_attempts,
                    idempotency_key,
                    error_code,
                    error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(job.id),
                    job.request_id,
                    job.job_type,
                    str(job.organisation_id)
                    if job.organisation_id
                    else None,
                    str(job.identity_id)
                    if job.identity_id
                    else None,
                    payload,
                    job.status,
                    job.scheduled_at.isoformat()
                    if job.scheduled_at
                    else None,
                    job.created_at.isoformat(),
                    None,
                    None,
                    None,
                    job.attempt_count,
                    job.max_attempts,
                    job.idempotency_key,
                    None,
                    None,
                ),
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self._audit_job(job, "JOB_ENQUEUED")
        return job

    def get(self, job_id: UUID) -> Job:
        row = self.db.execute(
            """
            SELECT
                id,
                request_id,
                job_type,
                organisation_id,
                identity_id,
                payload,
                status,
                scheduled_at,
                created_at,
                started_at,
                completed_at,
                failed_at,
                attempt_count,
                max_attempts,
                idempotency_key,
                error_code,
                error_message
            FROM jobs
            WHERE id = ?
            """,
            (str(job_id),),
        ).fetchone()

        if row is None:
            raise NotFoundError(f"Job '{job_id}' was not found.")

        payload = (
            json.loads(row["payload"])
            if row["payload"] is not None
            else None
        )

        return Job(
            id=UUID(row["id"]),
            request_id=row["request_id"],
            job_type=row["job_type"],
            organisation_id=(
                UUID(row["organisation_id"])
                if row["organisation_id"]
                else None
            ),
            identity_id=(
                UUID(row["identity_id"])
                if row["identity_id"]
                else None
            ),
            payload=payload,
            status=row["status"],
            scheduled_at=(
                datetime.fromisoformat(row["scheduled_at"])
                if row["scheduled_at"]
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=(
                datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            failed_at=(
                datetime.fromisoformat(row["failed_at"])
                if row["failed_at"]
                else None
            ),
            attempt_count=row["attempt_count"],
            max_attempts=row["max_attempts"],
            idempotency_key=row["idempotency_key"],
            error_code=row["error_code"],
            error_message=row["error_message"],
        )

    def list(
        self,
        organisation_id: UUID | None = None,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        valid_statuses = {
            "QUEUED",
            "RUNNING",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
        }

        if status is not None and status not in valid_statuses:
            raise ValidationError(f"Invalid job status: {status}")

        if limit < 1 or limit > 500:
            raise ValidationError("limit must be between 1 and 500.")

        if offset < 0:
            raise ValidationError("offset must be >= 0.")

        conditions = []
        params = []

        if organisation_id is not None:
            conditions.append("organisation_id = ?")
            params.append(str(organisation_id))

        if status is not None:
            conditions.append("status = ?")
            params.append(status)

        if job_type is not None:
            conditions.append("job_type = ?")
            params.append(job_type)

        where_clause = (
            "WHERE " + " AND ".join(conditions)
            if conditions
            else ""
        )

        rows = self.db.execute(
            f"""
            SELECT id
            FROM jobs
            {where_clause}
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()

        return [self.get(UUID(row["id"])) for row in rows]

    def get_due_jobs(
        self,
        organisation_id: UUID | None = None,
        job_type: str | None = None,
        limit: int = 100,
    ) -> List[Job]:
        """Return queued jobs that are currently eligible for execution."""

        if limit < 1 or limit > 500:
            raise ValidationError("limit must be between 1 and 500.")

        now = datetime.now(timezone.utc).isoformat()

        conditions = [
            "status = 'QUEUED'",
            "(scheduled_at IS NULL OR datetime(scheduled_at) <= datetime(?))",
        ]
        params = [now]

        if organisation_id is not None:
            conditions.append("organisation_id = ?")
            params.append(str(organisation_id))

        if job_type is not None:
            if not job_type.strip():
                raise ValidationError("job_type cannot be empty.")
            conditions.append("job_type = ?")
            params.append(job_type)

        where_clause = " AND ".join(conditions)

        rows = self.db.execute(
            f"""
            SELECT id
            FROM jobs
            WHERE {where_clause}
            ORDER BY
                CASE WHEN scheduled_at IS NULL THEN 0 ELSE 1 END,
                scheduled_at ASC,
                created_at ASC,
                id ASC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()

        return [self.get(UUID(row["id"])) for row in rows]

    def claim(self, job_id: UUID) -> Job:
        """Atomically claim a queued job that is eligible for execution."""

        now = datetime.now(timezone.utc)

        try:
            cursor = self.db.execute(
                """
                UPDATE jobs
                SET status = 'RUNNING',
                    started_at = ?,
                    attempt_count = attempt_count + 1
                WHERE id = ?
                  AND status = 'QUEUED'
                  AND (
                      scheduled_at IS NULL
                      OR datetime(scheduled_at) <= datetime(?)
                  )
                """,
                (
                    now.isoformat(),
                    str(job_id),
                    now.isoformat(),
                ),
            )

            if cursor.rowcount != 1:
                self.db.rollback()
                raise ConflictError(
                    "Job cannot be claimed because it is not queued "
                    "or is not yet scheduled."
                )

            self.db.commit()

        except ConflictError:
            raise
        except Exception:
            self.db.rollback()
            raise

        job = self.get(job_id)
        self._audit_job(job, "JOB_CLAIMED")
        return job

    def retry(self, job_id: UUID) -> Job:
        """Requeue a failed job when another execution attempt is allowed."""

        job = self.get(job_id)

        if job.status != "FAILED":
            raise ConflictError(
                "Job can only be retried when it is failed."
            )

        if job.attempt_count >= job.max_attempts:
            raise ConflictError(
                "Job cannot be retried because the maximum attempts have been reached."
            )

        try:
            self.db.execute(
                """
                UPDATE jobs
                SET status = 'QUEUED',
                    failed_at = NULL,
                    error_code = NULL,
                    error_message = NULL
                WHERE id = ?
                  AND status = 'FAILED'
                """,
                (str(job_id),),
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        job = self.get(job_id)
        self._audit_job(job, "JOB_RETRIED")
        return job

    def complete(self, job_id: UUID) -> Job:
        """Mark a running job as successfully completed."""

        now = datetime.now().astimezone().isoformat()

        try:
            cursor = self.db.execute(
                """
                UPDATE jobs
                SET status = 'COMPLETED',
                    completed_at = ?
                WHERE id = ?
                  AND status = 'RUNNING'
                """,
                (now, str(job_id)),
            )

            if cursor.rowcount != 1:
                self.db.rollback()
                raise ConflictError(
                    "Job cannot be completed because it is not running."
                )

            self.db.commit()

        except ConflictError:
            raise
        except Exception:
            self.db.rollback()
            raise

        job = self.get(job_id)
        self._audit_job(job, "JOB_COMPLETED")
        return job

    def fail(
        self,
        job_id: UUID,
        error_code: str,
        error_message: str,
    ) -> Job:
        """Mark a running job as failed."""

        if not error_code or not error_code.strip():
            raise ValidationError("error_code is required.")

        if not error_message or not error_message.strip():
            raise ValidationError("error_message is required.")

        now = datetime.now().astimezone().isoformat()

        try:
            cursor = self.db.execute(
                """
                UPDATE jobs
                SET status = 'FAILED',
                    failed_at = ?,
                    error_code = ?,
                    error_message = ?
                WHERE id = ?
                  AND status = 'RUNNING'
                """,
                (
                    now,
                    error_code.strip(),
                    error_message.strip(),
                    str(job_id),
                ),
            )

            if cursor.rowcount != 1:
                self.db.rollback()
                raise ConflictError(
                    "Job cannot be failed because it is not running."
                )

            self.db.commit()

        except ConflictError:
            raise
        except Exception:
            self.db.rollback()
            raise

        job = self.get(job_id)
        self._audit_job(job, "JOB_FAILED")
        return job
