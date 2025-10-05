"""Add ssn_full_hash and seed test patient

Revision ID: 8a9830b0907c
Revises: 
Create Date: 2025-10-04 13:20:19.203734

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, String, Date, DateTime
from datetime import date, datetime
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = 'add_ssn_hash_and_seed'
down_revision = None  # or set this to your previous revision id
branch_labels = None
depends_on = None

def upgrade():
    # add column iff missing (SQLite-friendly)
    conn = op.get_bind()
    cols = conn.exec_driver_sql("PRAGMA table_info('patient')").fetchall()
    has_col = any(c[1] == 'ssn_full_hash' for c in cols)  # c[1] = column name
    if not has_col:
        op.add_column('patient', sa.Column('ssn_full_hash', sa.String(length=255), nullable=True))

    # seed test patient (safe to re-run; uses constants)
    patient_tbl = table(
        'patient',
        column('first_name', String),
        column('last_name', String),
        column('dob', Date),
        column('ssn_last4', String),
        column('ssn_full_hash', String),
        column('created_at', DateTime),
    )

    op.bulk_insert(patient_tbl, [{
        'first_name': 'John',
        'last_name': 'Doe',
        'dob': date(1990, 5, 15),
        'ssn_last4': '6789',
        'ssn_full_hash': generate_password_hash("123-45-6789"),
        'created_at': datetime.utcnow(),
    }])

def downgrade():
    # Remove the seeded patient
    op.execute(
        "DELETE FROM patient WHERE first_name='John' AND last_name='Doe' AND dob='1990-05-15' AND ssn_last4='6789'"
    )
    op.drop_column('patient', 'ssn_full_hash')
