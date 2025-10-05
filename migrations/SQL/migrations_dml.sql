-- MATS manual SQL DML bundle (SQLite)
-- Run in DBeaver or: sqlite3 MATS.db < migrations_dml.sql
-- Notes:
--  * Uses conditional INSERTs to avoid duplicates.
--  * ALTER TABLE statements will fail if the column already exists; skip those if you've already added them.
--  * Replace the PASSWORD_HASH below with one generated in your venv:
--      from werkzeug.security import generate_password_hash
--      print(generate_password_hash("password", method="scrypt"))

BEGIN TRANSACTION;

-----------------------------------------------------------------------
-- 1) Seed dummy patient: John Doe (SSN last4 6789, DOB 1990-05-15)
-----------------------------------------------------------------------
INSERT INTO patient (first_name, last_name, dob, ssn_last4, ssn_full_hash, created_at)
SELECT 'John','Doe','1990-05-15','6789', 'REPLACE_WITH_FULL_SSN_HASH', CURRENT_TIMESTAMP
WHERE NOT EXISTS (
  SELECT 1 FROM patient
  WHERE first_name='John' AND last_name='Doe' AND dob='1990-05-15' AND ssn_last4='6789'
);

-----------------------------------------------------------------------
-- 2) Seed common medications (safe re-run)
-----------------------------------------------------------------------
INSERT INTO medication (name, strength)
SELECT 'Lisinopril','10 mg'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE name='Lisinopril' AND strength='10 mg');

INSERT INTO medication (name, strength)
SELECT 'Metformin','500 mg'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE name='Metformin' AND strength='500 mg');

INSERT INTO medication (name, strength)
SELECT 'Atorvastatin','20 mg'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE name='Atorvastatin' AND strength='20 mg');

INSERT INTO medication (name, strength)
SELECT 'Amlodipine','5 mg'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE name='Amlodipine' AND strength='5 mg');

INSERT INTO medication (name, strength)
SELECT 'Omeprazole','40 mg'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE name='Omeprazole' AND strength='40 mg');

-----------------------------------------------------------------------
-- 3) Seed prescriptions for John Doe (safe if patient/meds exist)
--    Creates 5 prescriptions starting today. Adjust as needed.
-----------------------------------------------------------------------
-- Lisinopril 10 mg, 1/day
INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes)
SELECT p.id, m.id, '1 tablet', 1, DATE('now'), 'seed'
FROM patient p, medication m
WHERE p.first_name='John' AND p.last_name='Doe' AND p.dob='1990-05-15'
  AND m.name='Lisinopril' AND m.strength='10 mg'
  AND NOT EXISTS (
      SELECT 1 FROM prescription pr
      WHERE pr.patient_id = p.id AND pr.medication_id = m.id
  );

-- Metformin 500 mg, 2/day
INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes)
SELECT p.id, m.id, '1 tablet', 2, DATE('now'), 'seed'
FROM patient p, medication m
WHERE p.first_name='John' AND p.last_name='Doe' AND p.dob='1990-05-15'
  AND m.name='Metformin' AND m.strength='500 mg'
  AND NOT EXISTS (
      SELECT 1 FROM prescription pr
      WHERE pr.patient_id = p.id AND pr.medication_id = m.id
  );

-- Atorvastatin 20 mg, 1/day
INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes)
SELECT p.id, m.id, '1 tablet', 1, DATE('now'), 'seed'
FROM patient p, medication m
WHERE p.first_name='John' AND p.last_name='Doe' AND p.dob='1990-05-15'
  AND m.name='Atorvastatin' AND m.strength='20 mg'
  AND NOT EXISTS (
      SELECT 1 FROM prescription pr
      WHERE pr.patient_id = p.id AND pr.medication_id = m.id
  );

-- Amlodipine 5 mg, 1/day
INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes)
SELECT p.id, m.id, '1 tablet', 1, DATE('now'), 'seed'
FROM patient p, medication m
WHERE p.first_name='John' AND p.last_name='Doe' AND p.dob='1990-05-15'
  AND m.name='Amlodipine' AND m.strength='5 mg'
  AND NOT EXISTS (
      SELECT 1 FROM prescription pr
      WHERE pr.patient_id = p.id AND pr.medication_id = m.id
  );

-- Omeprazole 40 mg, 1/day
INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes)
SELECT p.id, m.id, '1 capsule', 1, DATE('now'), 'seed'
FROM patient p, medication m
WHERE p.first_name='John' AND p.last_name='Doe' AND p.dob='1990-05-15'
  AND m.name='Omeprazole' AND m.strength='40 mg'
  AND NOT EXISTS (
      SELECT 1 FROM prescription pr
      WHERE pr.patient_id = p.id AND pr.medication_id = m.id
  );

-----------------------------------------------------------------------
-- 4) Add reminder flags (schema updates). Run ONLY if columns missing.
--    These will error if the column already exists. Skip if so.
-----------------------------------------------------------------------
-- Reminder on/off toggle (used in patient meds page)
/* RUN ONLY IF COLUMN NOT PRESENT */
ALTER TABLE prescription ADD COLUMN reminder_enabled BOOLEAN DEFAULT 0;

-- Record last reminder date for clinic dashboard "Today's Dosages"
/* RUN ONLY IF COLUMN NOT PRESENT */
ALTER TABLE prescription ADD COLUMN reminder_last_sent_date DATE;

-----------------------------------------------------------------------
-- 5) Seed/Update admin user (clinic staff)
--    Replace PASSWORD_HASH below with a scrypt hash from your venv.
-----------------------------------------------------------------------
-- Update if exists
UPDATE user
SET email = 'admin@example.com',
    password_hash = 'scrypt:32768:8:1$3V4hCyjYRB9oLiYX$743aa9059f30ea727ff2f6300a4c48a5161bfadbc5c98a823622d67adf32012b76034910dc2a28561e383b964d668f8b7a5b2540c9e378e69e0c9588bd92bbde'
WHERE username = 'admin';

-- Or create if missing
INSERT INTO user (username, email, password_hash, created_at)
SELECT 'admin', 'admin@example.com', 'scrypt:32768:8:1$3V4hCyjYRB9oLiYX$743aa9059f30ea727ff2f6300a4c48a5161bfadbc5c98a823622d67adf32012b76034910dc2a28561e383b964d668f8b7a5b2540c9e378e69e0c9588bd92bbde', CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM user WHERE username='admin');


COMMIT;