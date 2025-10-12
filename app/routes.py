
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from .forms import LoginForm, PatientForm, MedicationForm, PrescriptionForm, DoseLogForm, PatientLookupForm, PatientLoginForm
from .models import User, Patient, Medication, Prescription, DoseLog
from . import db
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


bp = Blueprint("main", __name__)

@bp.before_app_request
def require_auth_or_patient():

    allowed = {"main.patient_login", "main.clinic_login", "static"}

    if request.endpoint in allowed or request.endpoint is None:
        return

    if current_user.is_authenticated or session.get("active_patient_id"):
        return

    flash("You are signed out. Please Login", "warning")
    return redirect(url_for("main.patient_login"))

@bp.route("/", methods=["GET", "POST"])
def patient_login():
    form = PatientLoginForm()
    if form.validate_on_submit():
        digits = "".join(ch for ch in form.ssn_full.data if ch.isdigit())
        last4 = digits[-4:] if len(digits) >= 4 else None
        if not last4:
            flash("Please enter a valid SSN.", "warning")
            return render_template("patient_login.html", form=form)

        candidates = Patient.query.filter(
            Patient.ssn_last4 == last4,
            Patient.dob == form.dob.data
        ).all()
        valid = [p for p in candidates if p.ssn_full_hash and check_password_hash(p.ssn_full_hash, form.ssn_full.data)]
        if len(valid) == 1:
            session["active_patient_id"] = valid[0].id
            return redirect(url_for("main.medications"))
        elif len(valid) > 1:
            flash("Multiple matches found. Please contact support.", "danger")
        else:
            flash("No matching patient. Please check SSN and DOB.", "warning")
    return render_template("patient_login.html", form=form)    

@bp.route("/clinic_login", methods=["GET", "POST"])
def clinic_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        print(form.password.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for("main.clinic_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("clinic_login.html", form=form)


@bp.route("/clinic_dashboard")
@login_required
def clinic_dashboard():
    # --- original dashboard metrics ---
    patient_count = Patient.query.count()
    med_count = Medication.query.count()
    rx_count = Prescription.query.count()

    cutoff = datetime.utcnow() - timedelta(days=30)
    last_logs = (
        DoseLog.query
        .order_by(DoseLog.taken_at.desc())
        .limit(10)
        .all()
    )

    rows = (
        db.session.query(
            Patient.id,
            Patient.first_name,
            Patient.last_name,
            func.avg(db.case((DoseLog.was_taken == True, 1), else_=0)).label("adherence")
        )
        .join(Prescription, Prescription.patient_id == Patient.id)
        .join(DoseLog, DoseLog.prescription_id == Prescription.id)
        .filter(DoseLog.taken_at >= cutoff)
        .group_by(Patient.id)
        .order_by(func.avg(db.case((DoseLog.was_taken == True, 1), else_=0)).asc())
        .all()
    )

    recent_rx = (
        db.session.query(Prescription, Patient, Medication)
        .join(Patient, Prescription.patient_id == Patient.id)
        .join(Medication, Prescription.medication_id == Medication.id)
        .order_by(Prescription.id.desc())
        .limit(10)
        .all()
    )

    today = date.today()
    due_today = (
        db.session.query(Prescription, Patient, Medication)
        .join(Patient, Prescription.patient_id == Patient.id)
        .join(Medication, Prescription.medication_id == Medication.id)
        .filter(Prescription.start_date <= today)
        .filter((Prescription.end_date == None) | (Prescription.end_date >= today))
        .order_by(Patient.last_name.asc(), Medication.name.asc())
        .all()
    )

    # --- NEW: instantiate forms for the modals on this page ---
    patient_form = PatientForm()
    medication_form = MedicationForm()
    rx_form = PrescriptionForm()

    # If your PrescriptionForm has SelectFields, populate choices BEFORE render
    if hasattr(rx_form, "patient_id"):
        rx_form.patient_id.choices = [
            (p.id, f"{p.last_name}, {p.first_name}")
            for p in Patient.query.order_by(Patient.last_name.asc()).all()
        ]
    if hasattr(rx_form, "medication_id"):
        rx_form.medication_id.choices = [
            (m.id, f"{m.name} {m.strength or ''}".strip())
            for m in Medication.query.order_by(Medication.name.asc()).all()
        ]

    # --- render with everything needed by the template ---
    return render_template(
        "clinic_dashboard.html",
        patient_count=patient_count,
        med_count=med_count,
        rx_count=rx_count,
        last_logs=last_logs,
        rows=rows,
        recent_rx=recent_rx,
        due_today=due_today,
        today=today,
        # forms for modals
        patient_form=patient_form,
        medication_form=medication_form,
        rx_form=rx_form,
    )



@bp.route("/patients/new", methods=["POST"])
@login_required
def patient_new():
    form = PatientForm()

    if form.validate_on_submit():
        p = Patient()
        form.populate_obj(p)

        # --- Handle SSN securely ---
        digits = "".join(ch for ch in form.ssn_full.data if ch.isdigit())
        if len(digits) < 4:
            flash("Invalid SSN entered.", "warning")
            return redirect(url_for("main.clinic_dashboard"))

        p.ssn_last4 = digits[-4:]
        p.ssn_full_hash = generate_password_hash(form.ssn_full.data, method="scrypt")

        db.session.add(p)
        db.session.commit()
        flash(f"Patient {p.first_name} {p.last_name} added successfully.", "success")
    else:
        flash("Please correct the errors in the patient form.", "warning")

    return redirect(url_for("main.clinic_dashboard"))


@bp.route("/prescriptions/new", methods=["POST"])
@login_required
def prescription_new():
    form = PrescriptionForm()

    # IMPORTANT: if the form uses SelectField for patient_id / medication_id,
    # re-populate choices before validate so WTForms can validate data.
    if hasattr(form, "patient_id"):
        form.patient_id.choices = [
            (p.id, f"{p.last_name}, {p.first_name}") for p in Patient.query.order_by(Patient.last_name.asc()).all()
        ]
    if hasattr(form, "medication_id"):
        form.medication_id.choices = [
            (m.id, f"{m.name} {m.strength or ''}".strip()) for m in Medication.query.order_by(Medication.name.asc()).all()
        ]

    if form.validate_on_submit():
        rx = Prescription()
        form.populate_obj(rx)  # sets patient_id, medication_id, start_date, end_date, etc.
        db.session.add(rx)
        db.session.commit()
        flash("Prescription added.", "success")
    else:
        flash("Please fix the errors in the prescription form.", "warning")

    return redirect(url_for("main.clinic_dashboard"))



@bp.route("/logout")
def logout():
    if current_user.is_authenticated:

        logout_user()
        flash("You have been successfully logged out.", "success")
        return redirect(url_for("main.clinic_login"))

    if session.get("active_patient_id"):

        session.pop("active_patient_id", None)
        flash("Thank you. You have been successfully logged out.", "success")
        return redirect(url_for("main.patient_login"))


    flash("You are signed out.", "info")
    return redirect(url_for("main.patient_login"))



@bp.route("/medications")
def medications():
    active_pid = session.get("active_patient_id")
    if not active_pid:

        items = Medication.query.order_by(Medication.name.asc()).all()
        return render_template("medications.html", medications=items, patient=None, items=[], page=1, pages=1, total=0, per_page=5)

    patient = Patient.query.get(active_pid)
    page = request.args.get("page", 1, type=int)
    per_page = 5

    q = (db.session.query(Prescription, Medication)
         .join(Medication, Prescription.medication_id == Medication.id)
         .filter(Prescription.patient_id == active_pid)
         .order_by(Medication.name.asc()))

    total = q.count()
    items = q.limit(per_page).offset((page - 1) * per_page).all()


    now = datetime.utcnow()
    start_today = datetime(now.year, now.month, now.day)
    end_today = start_today + timedelta(days=1)

    rx_ids = [rx.id for rx, _ in items]
    logs_today = (DoseLog.query
                  .filter(DoseLog.prescription_id.in_(rx_ids),
                          DoseLog.taken_at >= start_today,
                          DoseLog.taken_at < end_today)
                  .all())
    clicked_today = {}
    logs_today_sorted = sorted(logs_today, key=lambda l: l.taken_at, reverse=True)
    for l in logs_today_sorted:
        if l.prescription_id not in clicked_today:
            clicked_today[l.prescription_id] = "taken" if l.was_taken else "missed"
    has_logged_today = {rid: False for rid in rx_ids}
    for l in logs_today:
        has_logged_today[l.prescription_id] = True

    active_today = {}
    today = date.today()
    for rx, _ in items:
        if rx.start_date and rx.end_date:
            active = rx.start_date <= today <= rx.end_date
        else:
            active = False
        active_today[rx.id] = active

    pages = (total + per_page - 1) // per_page if total else 1
    return render_template(
        "medications.html",
        patient=patient,
        items=items,
        page=page, pages=pages, total=total, per_page=per_page,
        has_logged_today=has_logged_today,
        active_today=active_today,
        today=today,
        clicked_today=clicked_today,   # <<---- pass to template
    )


@bp.route("/medications/take/<int:rx_id>", methods=["GET", "POST"])
def meds_take(rx_id):
    from app.services.adherence import was_taken_in_last_24h  # <-- add this import

    active_pid = session.get("active_patient_id")
    if not active_pid:
        flash("Please sign in as a patient.", "warning")
        return redirect(url_for("main.patient_login"))

    rx = Prescription.query.get_or_404(rx_id)
    if rx.patient_id != active_pid:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("main.medications"))

    today = date.today()
    is_active = ((rx.start_date is None or rx.start_date <= today) and
                 (rx.end_date is None or rx.end_date >= today))
    if not is_active:
        flash("This prescription is not active today (start/end date window).", "warning")
        return redirect(url_for("main.medications", page=request.args.get("page", 1)))

    # rolling 24-hour guard instead of func.date() ---
    if was_taken_in_last_24h(rx_id):
        flash("Already logged in the last 24 hours.", "warning")
        return redirect(url_for("main.medications", page=request.args.get("page", 1)))

    # If no recent dose, create one ---
    log = DoseLog(
        prescription_id=rx_id,
        taken_at=datetime.utcnow(),
        was_taken=True,
        notes="Taken within 24 hours"
    )
    db.session.add(log)
    db.session.commit()

    flash("Marked as taken.", "success")
    return redirect(url_for("main.medications", page=request.args.get("page", 1)))



@bp.route("/medications/new", methods=["GET", "POST"])
@login_required
def medication_new():
    form = MedicationForm()
    if form.validate_on_submit():
        m = Medication(name=form.name.data, strength=form.strength.data)
        db.session.add(m)
        db.session.commit()
        flash("Medication saved", "success")
        return redirect(url_for("main.medications"))
    return render_template("medication_form.html", form=form, title="New Medication")



@bp.post("/medications/miss/<int:rx_id>")
def meds_miss(rx_id):
    active_pid = session.get("active_patient_id")
    if not active_pid:
        flash("Please sign in as a patient.", "warning")
        return redirect(url_for("main.patient_login"))

    rx = Prescription.query.get_or_404(rx_id)
    if rx.patient_id != active_pid:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("main.medications"))

    today = date.today()
    is_active = (rx.start_date is None or rx.start_date <= today) and (rx.end_date is None or rx.end_date >= today)
    if not is_active:
        flash("This prescription is not active today (start/end date window).", "warning")
        return redirect(url_for("main.medications", page=request.args.get("page", 1)))

    log = DoseLog(prescription_id=rx_id, was_taken=False, notes="Missed today")
    db.session.add(log)
    db.session.commit()
    flash("Marked as missed for today.", "warning")
    return redirect(url_for("main.medications", page=request.args.get("page", 1)))


@bp.post("/medications/reminder/<int:rx_id>")
def meds_reminder(rx_id):
    active_pid = session.get("active_patient_id")
    if not active_pid:
        flash("Please sign in as a patient.", "warning")
        return redirect(url_for("main.patient_login"))

    rx = Prescription.query.get_or_404(rx_id)
    if rx.patient_id != active_pid:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("main.medications"))

    today = date.today()
    is_active = (rx.start_date and rx.end_date and rx.start_date <= today <= rx.end_date)
    if not is_active:
        flash("Cannot set a reminder for an inactive prescription.", "warning")
        return redirect(url_for("main.medications", page=request.args.get("page", 1)))

    med = Medication.query.get(rx.medication_id)

    rx.reminder_enabled = True
    db.session.commit()

    flash(f"Reminder set for: {med.name}", "success")
    return redirect(url_for("main.medications", page=request.args.get("page", 1)))



@bp.route("/clinic/reminder/<int:rx_id>", methods=["GET", "POST"])
@login_required
def clinic_send_reminder(rx_id):
    rx = Prescription.query.get_or_404(rx_id)
    p = Patient.query.get(rx.patient_id)
    m = Medication.query.get(rx.medication_id)

    rx.reminder_last_sent_date = date.today()
    db.session.commit()

    flash(f"Reminder sent to {p.first_name} {p.last_name} for today's dosage of {m.name}.", "success")
    return redirect(url_for("main.clinic_dashboard"))

@bp.route("/request-callback")
def request_callback():
    active_pid = session.get("active_patient_id")
    if not active_pid:
        flash("Please sign in as a patient.", "warning")
        return redirect(url_for("main.patient_login"))
    return render_template("request_callback.html")


@bp.route("/dose-history")
def dose_history():
    active_pid = session.get("active_patient_id")
    if not active_pid:
        flash("Please sign in as a patient.", "warning")
        return redirect(url_for("main.patient_login"))
    logs = (DoseLog.query
        .join(Prescription, DoseLog.prescription_id == Prescription.id)
        .filter(Prescription.patient_id == active_pid)
        .order_by(DoseLog.taken_at.desc())
        .all())
    return render_template("dose_history.html", logs=logs)

