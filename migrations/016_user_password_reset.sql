-- Add password reset state to users.
-- Idempotent because Phoenix currently replays all migrations at startup.

ALTER TABLE users
ADD COLUMN password_reset_required INTEGER NOT NULL DEFAULT 0
CHECK (password_reset_required IN (0,1));
