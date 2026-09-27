-- Phoenix Core
-- 035_company_user_role_uuid_fix.sql
--
-- Correct COMPANY.USER identifiers created by migration 034.
-- The original migration generated 32-character hex IDs while the
-- application expects UUID-formatted identifiers.

BEGIN;

UPDATE roles
SET id = '7b7f2e6c-0b9e-4a7e-9f1e-4f4c9b2d6a11'
WHERE id = 'f3e866fea13a01b537ede30db406f4e5'
  AND code = 'COMPANY.USER';

UPDATE roles
SET id = 'c3a1d8f4-5e72-4b91-8c36-2a7d6f9e1b54'
WHERE id = 'e8b65802356f979f5b41a7f326f762c6'
  AND code = 'COMPANY.USER';

COMMIT;
