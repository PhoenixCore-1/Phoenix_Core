-- Migration 020: IP Tenant Ownership Boundary
--
-- Company-owned IP/data must be explicitly bound to its tenant.
-- Platform/global owners remain organisation-independent.

ALTER TABLE ip_owners
    ADD COLUMN organisation_id TEXT;

CREATE INDEX IF NOT EXISTS ix_ip_owners_organisation
    ON ip_owners(organisation_id);

-- Existing owners created by Migration 019 are platform/global records.
-- COMPANY ownership records must be created with an organisation_id by the
-- IP service. SQLite cannot add a conditional CHECK to the existing table
-- without rebuilding it, so this invariant is enforced by the service layer
-- and tested explicitly.
