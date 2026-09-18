from uuid import uuid4

import pytest

from phoenix_core.errors import ConflictError, NotFoundError
from phoenix_core.infrastructure import SQLiteDatabase
from phoenix_core.jobs.contracts import JobExecutor, JobRequest
from phoenix_core.jobs.registry import JobExecutorRegistry
from phoenix_core.jobs.service import JobService
from phoenix_core.jobs.worker import JobWorker, WorkerResult
from phoenix_core.services import CoreFoundationService


class TestExecutor(JobExecutor):
    def execute(self, job_type, payload):
        return {
            "executed": job_type,
            "payload": payload,
        }


class FailingExecutor(JobExecutor):
    def execute(self, job_type, payload):
        raise RuntimeError("Intentional executor failure.")


def make_services(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))

    core = CoreFoundationService(db)
    core.initialise()

    job_service = JobService(db)
    registry = JobExecutorRegistry()
    worker = JobWorker(job_service, registry)

    return db, job_service, registry, worker


def test_worker_claims_executes_and_completes_job(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    registry.register("test.job", TestExecutor())

    job = service.enqueue(
        JobRequest(
            request_id="worker-001",
            job_type="test.job",
            payload={"value": 42},
        )
    )

    result = worker.process(job.id)

    assert isinstance(result, WorkerResult)
    assert result.job_id == job.id
    assert result.status == "COMPLETED"
    assert result.data == {
        "executed": "test.job",
        "payload": {"value": 42},
    }

    stored = service.get(job.id)

    assert stored.status == "COMPLETED"
    assert stored.attempt_count == 1
    assert stored.started_at is not None
    assert stored.completed_at is not None

    db.close()


def test_worker_passes_original_payload_to_executor(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    registry.register("payload.job", TestExecutor())

    payload = {
        "customer_id": "CUST-001",
        "amount": 123.45,
        "items": ["A", "B"],
    }

    job = service.enqueue(
        JobRequest(
            request_id="worker-002",
            job_type="payload.job",
            payload=payload,
        )
    )

    result = worker.process(job.id)

    assert result.data["payload"] == payload

    stored = service.get(job.id)
    assert stored.status == "COMPLETED"

    db.close()


def test_worker_failure_marks_job_failed(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    registry.register("failing.job", FailingExecutor())

    job = service.enqueue(
        JobRequest(
            request_id="worker-003",
            job_type="failing.job",
        )
    )

    with pytest.raises(RuntimeError, match="Intentional executor failure."):
        worker.process(job.id)

    stored = service.get(job.id)

    assert stored.status == "FAILED"
    assert stored.attempt_count == 1
    assert stored.started_at is not None
    assert stored.failed_at is not None
    assert stored.error_code == "RuntimeError"
    assert stored.error_message == "Intentional executor failure."

    db.close()


def test_worker_rejects_unknown_job_type_and_records_failure(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    job = service.enqueue(
        JobRequest(
            request_id="worker-004",
            job_type="unknown.job",
        )
    )

    with pytest.raises(NotFoundError):
        worker.process(job.id)

    stored = service.get(job.id)

    assert stored.status == "FAILED"
    assert stored.attempt_count == 1
    assert stored.failed_at is not None
    assert stored.error_code == "NotFoundError"

    db.close()


def test_worker_rejects_unknown_job_id(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    with pytest.raises(ConflictError):
        worker.process(uuid4())

    db.close()


def test_completed_job_cannot_be_processed_again(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    registry.register("single.job", TestExecutor())

    job = service.enqueue(
        JobRequest(
            request_id="worker-005",
            job_type="single.job",
        )
    )

    first = worker.process(job.id)

    assert first.status == "COMPLETED"

    with pytest.raises(ConflictError):
        worker.process(job.id)

    stored = service.get(job.id)

    assert stored.status == "COMPLETED"
    assert stored.attempt_count == 1

    db.close()


def test_worker_failure_does_not_complete_job(tmp_path):
    db, service, registry, worker = make_services(tmp_path)

    registry.register("failure.job", FailingExecutor())

    job = service.enqueue(
        JobRequest(
            request_id="worker-006",
            job_type="failure.job",
        )
    )

    with pytest.raises(RuntimeError):
        worker.process(job.id)

    stored = service.get(job.id)

    assert stored.status == "FAILED"
    assert stored.completed_at is None
    assert stored.failed_at is not None

    db.close()
