
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, Length, Regexp

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign In")

class PatientForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    dob = DateField("Date of Birth", validators=[DataRequired()])
    ssn_full = StringField(
        "Full SSN",
        validators=[
            DataRequired(),
            Regexp(r"^\d{9}$|^\d{3}-\d{2}-\d{4}$", message="Enter SSN as 9 digits or ###-##-####"),
        ],
    )
    submit = SubmitField("Save Patient")

class MedicationForm(FlaskForm):
    name = StringField("Medication Name", validators=[DataRequired(), Length(max=150)])
    strength = StringField("Strength", validators=[Optional(), Length(max=80)])
    submit = SubmitField("Save")

class PrescriptionForm(FlaskForm):
    patient_id = SelectField("Patient", coerce=int, validators=[DataRequired()])
    medication_id = SelectField("Medication", coerce=int, validators=[DataRequired()])
    dosage = StringField("Dosage", validators=[DataRequired(), Length(max=80)])
    frequency_per_day = IntegerField("Frequency / day", validators=[DataRequired(), NumberRange(min=1, max=24)])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save")

class DoseLogForm(FlaskForm):
    prescription_id = SelectField("Prescription", coerce=int, validators=[DataRequired()])
    was_taken = BooleanField("Dose Taken?", default=True)
    notes = StringField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Log Dose")


class PatientLookupForm(FlaskForm):
    ssn_last4 = StringField("SSN (last 4)", validators=[DataRequired(), Length(min=4, max=4)])
    dob = DateField("Date of Birth", validators=[DataRequired()])
    submit = SubmitField("Find")

class PatientLoginForm(FlaskForm):
    ssn_full = StringField("SSN", validators=[DataRequired(), Length(min=9, max=11)])  # accepts 123-45-6789 or 123456789
    dob = DateField("Date of Birth", validators=[DataRequired()])
    submit = SubmitField("Continue")