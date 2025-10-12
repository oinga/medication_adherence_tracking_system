# app/services/adherence.py
from sqlalchemy import exists, and_, select
from app import db
from app.models import DoseLog  # adjust import to your model location
from app.utils.timeutils import last_24h_window, local_day_bounds, utcnow

def was_taken_in_last_24h(prescription_id: int, now_utc=None) -> bool:
    start_utc, end_utc = last_24h_window(now_utc)
    stmt = select(exists().where(
        and_(
            DoseLog.prescription_id == prescription_id,
            DoseLog.taken_at >= start_utc,
            DoseLog.taken_at <  end_utc,
        )
    ))
    return db.session.execute(stmt).scalar()

def was_taken_on_calendar_day_local(prescription_id: int, now_utc=None) -> bool:
    """
    Useful for daily summary reports (still available if you need it).
    """
    start_utc, end_utc = local_day_bounds(now_utc)
    stmt = select(exists().where(
        and_(
            DoseLog.prescription_id == prescription_id,
            DoseLog.taken_at >= start_utc,
            DoseLog.taken_at <  end_utc,
        )
    ))
    return db.session.execute(stmt).scalar()
