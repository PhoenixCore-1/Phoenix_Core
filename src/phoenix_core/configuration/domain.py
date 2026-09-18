"""Domain models for Core configuration and feature flags."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from phoenix_core.errors import ValidationError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


SUPPORTED_VALUE_TYPES = {"STRING", "INTEGER", "NUMBER", "BOOLEAN", "JSON"}


@dataclass(frozen=True)
class SettingDefinition:
    id: UUID
    scope_type: str
    organisation_id: UUID | None
    key: str
    value_type: str
    value: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        key: str,
        value,
        value_type: str = "STRING",
        *,
        organisation_id: UUID | None = None,
        description: str | None = None,
    ) -> "SettingDefinition":
        key = key.strip()
        value_type = value_type.strip().upper()
        if not key:
            raise ValidationError("Setting key is required.")
        if value_type not in SUPPORTED_VALUE_TYPES:
            raise ValidationError("Unsupported setting value type.")
        if organisation_id is None:
            scope = "GLOBAL"
        else:
            scope = "ORGANISATION"
        encoded = encode_value(value, value_type)
        now = utcnow()
        return cls(uuid4(), scope, organisation_id, key, value_type, encoded, description, now, now)


@dataclass(frozen=True)
class FeatureFlag:
    id: UUID
    scope_type: str
    organisation_id: UUID | None
    key: str
    enabled: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        key: str,
        enabled: bool = False,
        *,
        organisation_id: UUID | None = None,
        description: str | None = None,
    ) -> "FeatureFlag":
        key = key.strip()
        if not key:
            raise ValidationError("Feature flag key is required.")
        if not isinstance(enabled, bool):
            raise ValidationError("Feature flag enabled must be boolean.")
        scope = "GLOBAL" if organisation_id is None else "ORGANISATION"
        now = utcnow()
        return cls(uuid4(), scope, organisation_id, key, enabled, description, now, now)


def encode_value(value, value_type: str) -> str:
    import json
    if value_type == "STRING":
        if not isinstance(value, str):
            raise ValidationError("STRING setting requires a string value.")
        return value
    if value_type == "INTEGER":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError("INTEGER setting requires an integer value.")
        return str(value)
    if value_type == "NUMBER":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError("NUMBER setting requires a numeric value.")
        return str(value)
    if value_type == "BOOLEAN":
        if not isinstance(value, bool):
            raise ValidationError("BOOLEAN setting requires a boolean value.")
        return "true" if value else "false"
    if value_type == "JSON":
        try:
            return json.dumps(value, separators=(",", ":"), sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise ValidationError("JSON setting value is not serializable.") from exc
    raise ValidationError("Unsupported setting value type.")


def decode_value(value: str, value_type: str):
    import json
    if value_type == "STRING":
        return value
    if value_type == "INTEGER":
        return int(value)
    if value_type == "NUMBER":
        return float(value)
    if value_type == "BOOLEAN":
        return value == "true"
    if value_type == "JSON":
        return json.loads(value)
    raise ValidationError("Unsupported setting value type.")
