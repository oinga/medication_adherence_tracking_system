
"""add reminder_enabled to prescription

Revision ID: add_reminder_column
Revises: seed_demo_meds
Create Date: 2025-10-04
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_reminder_column'
down_revision = 'seed_demo_meds'  # set to your actual previous revision id if different
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    # Add column only if missing (SQLite-safe)
    exists = conn.exec_driver_sql("PRAGMA table_info('prescription')").fetchall()
    names = [c[1] for c in exists]
    if 'reminder_enabled' not in names:
        op.add_column('prescription', sa.Column('reminder_enabled', sa.Boolean(), nullable=True))
        # Default to 0/False
        conn.exec_driver_sql("UPDATE prescription SET reminder_enabled = 0 WHERE reminder_enabled IS NULL")


def downgrade():
    # SQLite cannot drop columns easily without table rebuild; leave as no-op or implement rebuild if needed.
    pass
