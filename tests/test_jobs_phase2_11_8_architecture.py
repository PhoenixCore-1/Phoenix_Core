from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "phoenix_core"
JOBS = SRC / "jobs"


def test_jobs_package_exists():
    assert (JOBS / "__init__.py").exists()
    assert (JOBS / "contracts.py").exists()
    assert (JOBS / "domain.py").exists()
    assert (JOBS / "service.py").exists()
    assert (JOBS / "registry.py").exists()
    assert (JOBS / "worker.py").exists()
    assert (JOBS / "security.py").exists()


def test_job_infrastructure_does_not_import_api_layer():
    for filename in [
        "contracts.py",
        "domain.py",
        "service.py",
        "registry.py",
        "worker.py",
        "security.py",
    ]:
        text = (JOBS / filename).read_text(encoding="utf-8")
        assert "phoenix_core.api" not in text


def test_job_worker_does_not_contain_direct_sql():
    text = (JOBS / "worker.py").read_text(encoding="utf-8")
    assert "SELECT " not in text
    assert "INSERT " not in text
    assert "UPDATE " not in text
    assert "DELETE " not in text


def test_job_registry_is_framework_independent():
    text = (JOBS / "registry.py").read_text(encoding="utf-8")
    assert "flask" not in text.lower()
    assert "django" not in text.lower()
    assert "fastapi" not in text.lower()


def test_job_security_reuses_core_authority():
    text = (JOBS / "security.py").read_text(encoding="utf-8")
    assert "effective_permissions" in text
    assert "module_available" in text
    assert "organisation_memberships" in text


def test_job_service_uses_core_audit_authority():
    text = (JOBS / "service.py").read_text(encoding="utf-8")
    assert "from phoenix_core.audit.domain import AuditEvent" in text
    assert "from phoenix_core.audit.service import AuditService" in text
    assert "class JobAudit" not in text
    assert "JOB_ENQUEUED" in text
    assert "JOB_CLAIMED" in text
    assert "JOB_RETRIED" in text
    assert "JOB_COMPLETED" in text
    assert "JOB_FAILED" in text
