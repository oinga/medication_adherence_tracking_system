"""Seed core data, add reminder columns, admin user, and hardening indexes (idempotent)."""

from alembic import op
from sqlalchemy import text
from datetime import date

# --- Revision identifiers ---
revision = "seed_and_hardening"
down_revision = "add_reminder_column"  # e.g., "8a9830b0907c"
branch_labels = None
depends_on = None


# ---------- helpers ----------
def _column_exists(conn, table: str, col: str) -> bool:
    """
    SQLite PRAGMAs do NOT accept bound params. Build literal safely.
    Row format: (cid, name, type, notnull, dflt_value, pk)
    """
    safe_table = table.replace("'", "''")
    rows = conn.exec_driver_sql(f"PRAGMA table_info('{safe_table}')").fetchall()
    return any(r[1] == col for r in rows)


def upgrade():
    conn = op.get_bind()

    # 1) Add reminder columns to prescription (safe/idempotent)
    if not _column_exists(conn, "prescription", "reminder_enabled"):
        conn.exec_driver_sql(
            "ALTER TABLE prescription ADD COLUMN reminder_enabled BOOLEAN DEFAULT 0"
        )
    if not _column_exists(conn, "prescription", "reminder_last_sent_date"):
        conn.exec_driver_sql(
            "ALTER TABLE prescription ADD COLUMN reminder_last_sent_date DATE"
        )

    # 2) Seed a demo patient (idempotent)
    conn.exec_driver_sql(
        """
        INSERT INTO patient (first_name, last_name, dob, ssn_last4, ssn_full_hash, created_at)
        SELECT 'John','Doe','1990-05-15','6789','REPLACE_WITH_FULL_SSN_HASH', DATE('now')
        WHERE NOT EXISTS (
          SELECT 1 FROM patient
          WHERE first_name='John' AND last_name='Doe' AND ssn_last4='6789'
        );
        """
    )

    # 3) Seed medications (idempotent)
    meds = [
        ("Lisinopril", "10 mg"),
        ("Atorvastatin", "20 mg"),
        ("Metformin", "500 mg"),
        ("Amlodipine", "5 mg"),
        ("Levothyroxine", "50 mcg"),
    ]
    for name, strength in meds:
        conn.exec_driver_sql(
            """
            INSERT INTO medication (name, strength)
            SELECT :name, :strength
            WHERE NOT EXISTS (
              SELECT 1 FROM medication WHERE name=:name AND strength=:strength
            );
            """,
            {"name": name, "strength": strength},
        )

    # 4) Seed demo prescriptions for John Doe (idempotent)
    conn.exec_driver_sql(
        """
        INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes, reminder_enabled)
        SELECT p.id, m.id, '1 tab', 1, DATE('now'), 'Seed prescription', 0
        FROM patient p
        JOIN medication m ON m.name='Lisinopril' AND m.strength='10 mg'
        WHERE p.first_name='John' AND p.last_name='Doe' AND p.ssn_last4='6789'
          AND NOT EXISTS (
            SELECT 1 FROM prescription pr
            WHERE pr.patient_id = p.id AND pr.medication_id = m.id
          );
        """
    )
    conn.exec_driver_sql(
        """
        INSERT INTO prescription (patient_id, medication_id, dosage, frequency_per_day, start_date, notes, reminder_enabled)
        SELECT p.id, m.id, '1 tab', 1, DATE('now'), 'Seed prescription', 0
        FROM patient p
        JOIN medication m ON m.name='Metformin' AND m.strength='500 mg'
        WHERE p.first_name='John' AND p.last_name='Doe' AND p.ssn_last4='6789'
          AND NOT EXISTS (
            SELECT 1 FROM prescription pr
            WHERE pr.patient_id = p.id AND pr.medication_id = m.id
          );
        """
    )

    # 5) Upsert admin user with scrypt hash (idempotent)
    #    Generate in venv:
    #    >>> from werkzeug.security import generate_password_hash
    #    >>> print(generate_password_hash("password", method="scrypt"))
    SCRYPT_HASH = "scrypt:32768:8:1$3V4hCyjYRB9oLiYX$743aa9059f30ea727ff2f6300a4c48a5161bfadbc5c98a823622d67adf32012b76034910dc2a28561e383b964d668f8b7a5b2540c9e378e69e0c9588bd92bbde"  # e.g., scrypt:32768:8:1$...$...

    # Insert admin if missing
    conn.exec_driver_sql(
        """
        INSERT INTO "user" (username, email, password_hash, created_at)
        SELECT 'admin','admin@example.com', :hash, DATE('now')
        WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE username='admin' OR email='admin@example.com');
        """,
        {"hash": SCRYPT_HASH},
    )
    # If present but placeholder/empty, update hash
    conn.exec_driver_sql(
        """
        UPDATE "user"
        SET password_hash=:hash
        WHERE email='admin@example.com'
          AND (password_hash IS NULL OR password_hash='' OR password_hash LIKE 'REPLACE_WITH%');
        """,
        {"hash": SCRYPT_HASH},
    )

    # 6) Hardening: dedupe and unique indexes (idempotent)
    #    A) DoseLog: keep earliest row per (prescription_id, date(taken_at))
    conn.exec_driver_sql(
        """
        DELETE FROM dose_log
        WHERE rowid IN (
          SELECT dl.rowid
          FROM dose_log dl
          JOIN (
            SELECT prescription_id AS pid,
                   date(taken_at)  AS dday,
                   MIN(rowid)      AS keep_rowid,
                   COUNT(*)        AS cnt
            FROM dose_log
            GROUP BY pid, dday
            HAVING cnt > 1
          ) dup
            ON dup.pid  = dl.prescription_id
           AND dup.dday = date(dl.taken_at)
          WHERE dl.rowid <> dup.keep_rowid
        );
        """
    )
    #    B) Unique per day per Rx (SQLite expression index)
    conn.exec_driver_sql(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_dose_log_rx_day
        ON dose_log (prescription_id, date(taken_at));
        """
    )
    #    C) Unique medication (name, strength)
    conn.exec_driver_sql(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_medication_name_strength
        ON medication (name, strength);
        """
    )


def downgrade():
    conn = op.get_bind()
    # Drop indexes created here (safe if absent)
    conn.exec_driver_sql("DROP INDEX IF EXISTS uq_dose_log_rx_day;")
    conn.exec_driver_sql("DROP INDEX IF EXISTS uq_medication_name_strength;")
    # We do not attempt to remove columns/data due to SQLite limitations and safety.
