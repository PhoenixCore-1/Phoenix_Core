PRAGMA foreign_keys = ON;

ALTER TABLE production_bom_versions
ADD COLUMN spc_definition_id TEXT;

CREATE INDEX idx_production_bom_versions_spc_definition
ON production_bom_versions(spc_definition_id);
