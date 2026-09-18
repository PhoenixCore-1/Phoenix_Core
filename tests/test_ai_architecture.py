from pathlib import Path


AI_ROOT = Path("src/phoenix_core/ai")


def python_files():
    return [
        path
        for path in AI_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    ]


def test_ai_does_not_import_business_modules():
    forbidden = (
        "phoenix_modules",
        "phoenix_core.modules.production",
        "phoenix_core.modules.crm",
        "phoenix_core.modules.sales",
        "phoenix_core.modules.inventory",
        "phoenix_core.modules.procurement",
        "phoenix_core.modules.accounts",
        "production",
        "crm",
        "sales",
        "inventory",
        "procurement",
        "accounts",
    )

    violations = []

    for path in python_files():
        text = path.read_text(encoding="utf-8")

        for forbidden_import in forbidden:
            if forbidden_import in text:
                violations.append(
                    f"{path}: {forbidden_import}"
                )

    assert not violations, "\n".join(violations)


def test_ai_does_not_contain_direct_sql():
    sql_markers = (
        "SELECT ",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "CREATE TABLE",
        "DROP TABLE",
    )

    violations = []

    for path in python_files():
        text = path.read_text(encoding="utf-8").upper()

        for marker in sql_markers:
            if marker in text:
                violations.append(
                    f"{path}: {marker}"
                )

    assert not violations, "\n".join(violations)


def test_ai_does_not_define_duplicate_security_authority():
    forbidden_names = (
        "IdentityService",
        "TenantService",
        "OrganisationService",
        "PermissionService",
        "MembershipService",
        "AuthenticationService",
        "SessionService",
    )

    violations = []

    for path in python_files():
        text = path.read_text(encoding="utf-8")

        for name in forbidden_names:
            if f"class {name}" in text:
                violations.append(
                    f"{path}: {name}"
                )

    assert not violations, "\n".join(violations)


def test_ai_provider_credentials_are_not_hardcoded():
    """Provider secrets must come from the Core SecretResolver boundary."""

    forbidden_patterns = (
        "sk-",
        "sk-proj-",
        "sk-ant-",
        "AIza",
        "ANTHROPIC_API_KEY=",
        "GEMINI_API_KEY=",
    )

    violations = []

    for path in python_files():
        text = path.read_text(encoding="utf-8")

        for pattern in forbidden_patterns:
            if pattern in text:
                violations.append(
                    f"{path}: {pattern}"
                )

    assert not violations, "\n".join(violations)


def test_openai_provider_uses_secret_resolver():
    path = AI_ROOT / "providers" / "openai.py"
    text = path.read_text(encoding="utf-8")

    assert "SecretResolver" in text
    assert "secret_resolver.get_secret" in text
