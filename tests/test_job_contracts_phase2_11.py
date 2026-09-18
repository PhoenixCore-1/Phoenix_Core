from datetime import datetime, timezone
from uuid import uuid4

from phoenix_core.jobs.contracts import JobExecutor, JobRequest, JobResult


def test_job_request_is_immutable():
    organisation_id = uuid4()
    identity_id = uuid4()
    scheduled_at = datetime.now(timezone.utc)

    request = JobRequest(
        request_id="req-job-001",
        job_type="example.operation",
        organisation_id=organisation_id,
        identity_id=identity_id,
        payload={"value": 123},
        scheduled_at=scheduled_at,
        idempotency_key="job-001",
    )

    assert request.request_id == "req-job-001"
    assert request.job_type == "example.operation"
    assert request.organisation_id == organisation_id
    assert request.identity_id == identity_id
    assert request.payload == {"value": 123}
    assert request.scheduled_at == scheduled_at
    assert request.idempotency_key == "job-001"

    try:
        request.job_type = "changed"
        assert False, "Expected frozen JobRequest"
    except AttributeError:
        pass


def test_job_result_is_immutable():
    job_id = uuid4()

    result = JobResult(
        request_id="req-job-002",
        job_id=job_id,
        status="QUEUED",
        data={"accepted": True},
    )

    assert result.request_id == "req-job-002"
    assert result.job_id == job_id
    assert result.status == "QUEUED"
    assert result.data["accepted"] is True

    try:
        result.status = "FAILED"
        assert False, "Expected frozen JobResult"
    except AttributeError:
        pass


def test_job_executor_defines_framework_independent_contract():
    class ExampleExecutor(JobExecutor):
        def execute(self, job_type, payload):
            return {
                "job_type": job_type,
                "payload": payload,
            }

    executor = ExampleExecutor()

    result = executor.execute(
        "example.operation",
        {"value": 123},
    )

    assert result["job_type"] == "example.operation"
    assert result["payload"]["value"] == 123
