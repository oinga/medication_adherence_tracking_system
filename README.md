# Medical Adherence Tracking System (MATS)

## Author
**Ortiv Inga**  
Developed as part of the MSIT Capstone Project at **University of the People™**

---

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Test Accounts](#test-accounts)
8. [Testing](#testing)
9. [Project Structure](#project-structure)
10. [Credits](#credits)
11. [License](#license)

---

## Overview
The **Medical Adherence Tracking System** or **MATS** is an application based in the Flask micro-framework. It serves to connect healthcare providers and patients towards the management and tracking of medication adherence in a secure and efficient manner. The application has separate portals for patients and clinics to document, track, and manage medication schedules while ensuring data secretiveness and security.

MATS was created during my MSIT Capstone Project and is compliant with software engineering best practices concerning usability, scalability, and security. The system provides authentication, authorization, role-based dashboards, and much more, a comprehensive and efficient audit logging module for ensuring compliance and reliability.

---

## Features
- Secure patient and clinic login portals  
- Role-based access control for data segregation  
- Medication logging, dose tracking, and reminders  
- Administrative dashboard for clinical oversight  
- Database migrations using Alembic  
- Integrated test suite using `pytest` for validation and security checks  
- CSRF-protected forms and password hashing (SCRYPT)

---

## System Requirements
- **Python:** 3.10+  
- **Flask:** 2.3+  
- **Database:** SQLite (default) or compatible SQLAlchemy backend  
- **Dependencies:** Listed in `requirements.txt`

---

## Installation

```bash
# Clone the repository
git clone https://github.com/OrtivInga/MATS.git
cd MATS

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Default configuration uses SQLite.  
For custom environments, update `config.py` accordingly.

Example environment variables (optional):
```bash
export FLASK_ENV=development
export DATABASE_URL=sqlite:///instance/MATS.db
```

---

## Running the Application

To initialize and start the app:

```bash
# Initialize database
flask db upgrade

# Seed data (optional)
python migrate_db.py

# Run the Flask app
python app.py
```

Visit [http://localhost:5000](http://localhost:5000) to access the web interface.

---

## Test Accounts

The following demo credentials are provided for evaluation and local testing purposes only.  
They are created automatically when running the seed script (`migrate_db.py`) or can be added manually via SQLite.

### Clinic Admin Login
- **Username:** `test_admin`  
- **Password:** `password`  

This account provides access to the clinic dashboard and administrative routes such as `/clinic_dashboard`, `/clinic/reminder/<id>`, and medication oversight features.

### Patient Login
- **SSN:** `123-45-6789`  
- **Date of Birth:** `1990-01-01`  

This patient account can be used to access patient-facing routes such as `/medications`, `/dose-history`, and `/request-callback`.

⚠️ *These credentials do not correspond to real data, and should never be used in production environments.*

---

## Testing

MATS includes an automated test suite powered by **pytest** with HTML reporting for coverage verification.

To run the tests:

```bash
pytest -q --html=tests_report.html --self-contained-html
```

This will generate a `tests_report.html` file containing all test outcomes, log traces, and security validation results.  

---

## Project Structure

```
MATS/
├── app/
│   ├── static/
│   ├── templates/
│   ├── SQL/
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   └── __init__.py
├── instance/
│   └── MATS.db
├── migrations/
├── tests/
│   ├── test_auth.py
│   ├── test_meds_and_adherence.py
│   ├── test_patient_scope.py
│   └── test_reminders.py
├── config.py
├── migrate_db.py
├── requirements.txt
└── app.py
```

---

## Credits
- **Author:** Ortiv Inga  
- **Institution:** University of the People™  
- **Special Thanks:** Faculty and peers from the MSIT Capstone course for guidance and technical review.

---

## License
This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

You are free to use, modify, and distribute this software under the terms of the license.  
For more details, see [GNU GPLv3 License](https://www.gnu.org/licenses/gpl-3.0.en.html).
