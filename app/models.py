
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from datetime import datetime, timedelta

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    ssn_last4 = db.Column(db.String(4), nullable=True, index=True)
    ssn_full_hash = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    prescriptions = db.relationship("Prescription", backref="patient", lazy=True, cascade="all, delete-orphan")

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    strength = db.Column(db.String(80), nullable=True)

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey("medication.id"), nullable=False)
    dosage = db.Column(db.String(80), nullable=False) # e.g., "1 tablet"
    frequency_per_day = db.Column(db.Integer, nullable=False) # e.g., 2 times/day
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    medication = db.relationship("Medication", backref="prescriptions", lazy=True)
    reminder_enabled = db.Column(db.Boolean, default=False)
    reminder_last_sent_date = db.Column(db.Date, nullable=True)


class DoseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey("prescription.id"), nullable=False)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    was_taken = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(255), nullable=True)
    prescription = db.relationship("Prescription", backref="dose_logs", lazy=True)

    @staticmethod
    def adherence_for_prescription(prescription: "Prescription") -> float:
        # No start date -> no expectation / no score
        if not prescription.start_date:
            return 0.0

        # Use today's date, and don't project beyond today
        today = datetime.utcnow().date()
        end = prescription.end_date or today
        end = min(end, today)

        # If the prescription ends before it starts (bad data), short-circuit
        if end < prescription.start_date:
            return 0.0

        # Inclusive day count
        days = (end - prescription.start_date).days + 1
        freq = prescription.frequency_per_day or 1
        expected = max(days * max(freq, 1), 0)

        # Build naive UTC bounds [start_dt, end_dt) — end is exclusive, so add a day
        start_dt = datetime.combine(prescription.start_date, datetime.min.time())
        end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time())

        # Count only taken doses within the active window
        taken = DoseLog.query.filter(
            DoseLog.prescription_id == prescription.id,
            DoseLog.was_taken.is_(True),
            DoseLog.taken_at >= start_dt,
            DoseLog.taken_at <  end_dt,
        ).count()

        return (taken / expected) * 100.0 if expected else 0.0
