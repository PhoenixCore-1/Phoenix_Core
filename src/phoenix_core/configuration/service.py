"""Core-owned configuration and feature flag application services."""

from datetime import datetime
from uuid import UUID

from phoenix_core.configuration.domain import FeatureFlag, SettingDefinition, decode_value, encode_value
from phoenix_core.errors import ConflictError, NotFoundError, ValidationError
from phoenix_core.infrastructure import SQLiteDatabase


class ConfigurationService:
    """Owns persistent Core settings and feature flags."""

    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def set_setting(self, setting: SettingDefinition) -> SettingDefinition:
        if setting.organisation_id is not None:
            self._require_active_organisation(setting.organisation_id)
        existing = self.db.execute(
            "SELECT id FROM core_settings WHERE scope_type=? AND COALESCE(organisation_id,'')=COALESCE(?, '') AND key=?",
            (setting.scope_type, str(setting.organisation_id) if setting.organisation_id else None, setting.key),
        ).fetchone()
        now = datetime.now(setting.created_at.tzinfo or __import__('datetime').timezone.utc).isoformat()
        if existing:
            self.db.execute(
                "UPDATE core_settings SET value_type=?, value=?, description=?, updated_at=? WHERE id=?",
                (setting.value_type, setting.value, setting.description, now, existing["id"]),
            )
        else:
            self.db.execute(
                "INSERT INTO core_settings (id,scope_type,organisation_id,key,value_type,value,description,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (str(setting.id), setting.scope_type, str(setting.organisation_id) if setting.organisation_id else None,
                 setting.key, setting.value_type, setting.value, setting.description, setting.created_at.isoformat(), now),
            )
        self.db.commit()
        return self.get_setting(setting.key, organisation_id=setting.organisation_id)

    def create_setting(self, key, value, value_type="STRING", *, organisation_id=None, description=None):
        setting = SettingDefinition.create(key, value, value_type, organisation_id=organisation_id, description=description)
        return self.set_setting(setting)

    def get_setting(self, key: str, *, organisation_id: UUID | None = None, required: bool = True):
        key = key.strip()
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
        row = self.db.execute(
            "SELECT * FROM core_settings WHERE scope_type=? AND COALESCE(organisation_id,'')=COALESCE(?, '') AND key=?",
            ("ORGANISATION" if organisation_id else "GLOBAL", str(organisation_id) if organisation_id else None, key),
        ).fetchone()
        if not row:
            if required:
                raise NotFoundError("Core setting not found.")
            return None
        return self._setting_from_row(row)

    def get_effective_setting(self, key: str, *, organisation_id: UUID | None = None, required: bool = True):
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
            row = self.db.execute(
                "SELECT * FROM core_settings WHERE scope_type='ORGANISATION' AND organisation_id=? AND key=?",
                (str(organisation_id), key.strip()),
            ).fetchone()
            if row:
                return self._setting_from_row(row)
        row = self.db.execute(
            "SELECT * FROM core_settings WHERE scope_type='GLOBAL' AND organisation_id IS NULL AND key=?",
            (key.strip(),),
        ).fetchone()
        if not row:
            if required:
                raise NotFoundError("Core setting not found.")
            return None
        return self._setting_from_row(row)

    def list_settings(self, *, organisation_id: UUID | None = None, include_global: bool = False):
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
        if organisation_id is not None and include_global:
            rows = self.db.execute(
                "SELECT * FROM core_settings WHERE (scope_type='GLOBAL' AND organisation_id IS NULL) OR (scope_type='ORGANISATION' AND organisation_id=?) ORDER BY key",
                (str(organisation_id),),
            ).fetchall()
        elif organisation_id is not None:
            rows = self.db.execute("SELECT * FROM core_settings WHERE scope_type='ORGANISATION' AND organisation_id=? ORDER BY key", (str(organisation_id),)).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM core_settings WHERE scope_type='GLOBAL' AND organisation_id IS NULL ORDER BY key").fetchall()
        return [self._setting_from_row(row) for row in rows]

    def create_feature_flag(self, key, enabled=False, *, organisation_id=None, description=None):
        flag = FeatureFlag.create(key, enabled, organisation_id=organisation_id, description=description)
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
        existing = self.db.execute(
            "SELECT id FROM feature_flags WHERE scope_type=? AND COALESCE(organisation_id,'')=COALESCE(?, '') AND key=?",
            (flag.scope_type, str(organisation_id) if organisation_id else None, key.strip()),
        ).fetchone()
        if existing:
            raise ConflictError("Feature flag already exists in this scope.")
        self.db.execute(
            "INSERT INTO feature_flags (id,scope_type,organisation_id,key,enabled,description,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (str(flag.id), flag.scope_type, str(organisation_id) if organisation_id else None, flag.key, 1 if flag.enabled else 0, flag.description, flag.created_at.isoformat(), flag.updated_at.isoformat()),
        )
        self.db.commit()
        return flag

    def set_feature_flag(self, key: str, enabled: bool, *, organisation_id=None):
        if not isinstance(enabled, bool):
            raise ValidationError("Feature flag enabled must be boolean.")
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
        row = self.db.execute(
            "SELECT * FROM feature_flags WHERE scope_type=? AND COALESCE(organisation_id,'')=COALESCE(?, '') AND key=?",
            ("ORGANISATION" if organisation_id else "GLOBAL", str(organisation_id) if organisation_id else None, key.strip()),
        ).fetchone()
        if not row:
            raise NotFoundError("Feature flag not found.")
        self.db.execute("UPDATE feature_flags SET enabled=?, updated_at=? WHERE id=?", (1 if enabled else 0, datetime.now().astimezone().isoformat(), row["id"]))
        self.db.commit()
        return self._flag_from_row(self.db.execute("SELECT * FROM feature_flags WHERE id=?", (row["id"],)).fetchone())

    def get_feature_flag(self, key: str, *, organisation_id=None, required=True):
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
        row = self.db.execute(
            "SELECT * FROM feature_flags WHERE scope_type=? AND COALESCE(organisation_id,'')=COALESCE(?, '') AND key=?",
            ("ORGANISATION" if organisation_id else "GLOBAL", str(organisation_id) if organisation_id else None, key.strip()),
        ).fetchone()
        if not row:
            if required:
                raise NotFoundError("Feature flag not found.")
            return None
        return self._flag_from_row(row)

    def is_feature_enabled(self, key: str, *, organisation_id=None) -> bool:
        if organisation_id is not None:
            self._require_active_organisation(organisation_id)
            row = self.db.execute(
                "SELECT enabled FROM feature_flags WHERE scope_type='ORGANISATION' AND organisation_id=? AND key=?",
                (str(organisation_id), key.strip()),
            ).fetchone()
            if row is not None:
                return bool(row["enabled"])
        row = self.db.execute("SELECT enabled FROM feature_flags WHERE scope_type='GLOBAL' AND organisation_id IS NULL AND key=?", (key.strip(),)).fetchone()
        return bool(row["enabled"]) if row is not None else False

    def _require_active_organisation(self, organisation_id: UUID):
        row = self.db.execute("SELECT status FROM organisations WHERE id=?", (str(organisation_id),)).fetchone()
        if not row:
            raise ValidationError("Organisation does not exist.")
        if row["status"] != "ACTIVE":
            raise ValidationError("Organisation must be active.")

    @staticmethod
    def _setting_from_row(row):
        return SettingDefinition(UUID(row["id"]), row["scope_type"], UUID(row["organisation_id"]) if row["organisation_id"] else None,
                                 row["key"], row["value_type"], row["value"], row["description"],
                                 datetime.fromisoformat(row["created_at"]), datetime.fromisoformat(row["updated_at"]))

    @staticmethod
    def _flag_from_row(row):
        return FeatureFlag(UUID(row["id"]), row["scope_type"], UUID(row["organisation_id"]) if row["organisation_id"] else None,
                           row["key"], bool(row["enabled"]), row["description"], datetime.fromisoformat(row["created_at"]), datetime.fromisoformat(row["updated_at"]))
