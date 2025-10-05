
"""seed demo meds and prescriptions for John Doe

Revision ID: seed_demo_meds
Revises: add_ssn_hash_and_seed
Create Date: 2025-10-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from datetime import date, timedelta

# revision identifiers, used by Alembic.
revision = 'seed_demo_meds'
down_revision = 'add_ssn_hash_and_seed'  # update if your previous id differs
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()

    # Find John Doe from prior seed
    pid = conn.exec_driver_sql(
        """SELECT id FROM patient
             WHERE first_name='John' AND last_name='Doe'
               AND dob='1990-05-15' AND ssn_last4='6789'""").scalar()

    if not pid:
        return  # nothing to seed against

    # Ensure medications exist (insert if missing)
    meds = [
        ('Lisinopril', '10 mg'),
        ('Metformin', '500 mg'),
        ('Atorvastatin', '20 mg'),
        ('Amoxicillin', '500 mg'),
        ('Albuterol', '90 mcg')
    ]

    for name, strength in meds:
        conn.exec_driver_sql(
            """INSERT INTO medication (name, strength)
                 SELECT :n, :s
                 WHERE NOT EXISTS (
                   SELECT 1 FROM medication WHERE name = :n AND strength = :s
                 )""",
            dict(n=name, s=strength)
        )

    # Pull medication ids
    rows = conn.exec_driver_sql("SELECT id, name, strength FROM medication").mappings().all()
    med_index = {(r['name'], r['strength']): r['id'] for r in rows}

    # Seed prescriptions linked to John Doe
    today = date.today()
    start = today - timedelta(days=30)

    presc = [
        ('Lisinopril', '10 mg', '1 tablet', 1),
        ('Metformin', '500 mg', '1 tablet', 2),
        ('Atorvastatin', '20 mg', '1 tablet', 1),
        ('Albuterol', '90 mcg', '2 puffs', 3),
        ('Amoxicillin', '500 mg', '1 capsule', 2),
    ]

    for name, strength, dosage, freq in presc:
        mid = med_index.get((name, strength))
        if not mid:
            continue
        conn.exec_driver_sql(
            """INSERT INTO prescription
                    (patient_id, medication_id, dosage, frequency_per_day, start_date, end_date, notes)
                 VALUES (:pid, :mid, :dosage, :freq, :start, NULL, :notes)""",
            dict(pid=pid, mid=mid, dosage=dosage, freq=freq, start=start.isoformat(), notes='seed')
        )

def downgrade():
    conn = op.get_bind()
    # Remove seeded prescriptions for John Doe
    pid = conn.exec_driver_sql(
        """SELECT id FROM patient
             WHERE first_name='John' AND last_name='Doe'
               AND dob='1990-05-15' AND ssn_last4='6789'""").scalar()
    if pid:
        conn.exec_driver_sql("DELETE FROM prescription WHERE patient_id = :pid", dict(pid=pid))
