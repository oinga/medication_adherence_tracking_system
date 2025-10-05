# tests/test_reminders.py
import logging
logger = logging.getLogger(__name__)

def test_patient_side_reminder_endpoint_not_open_to_anonymous(client):
    logger.info("GET /medications/reminder/1 (unauthenticated) -> expect 405 or protected redirect")
    r = client.get("/medications/reminder/1", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (405, 302, 401, 403), f"Expected 405/redirect; got {r.status_code}"

def test_clinic_send_reminder_requires_login(client):
    logger.info("GET /clinic/reminder/1 (unauthenticated) -> expect redirect/forbidden")
    r = client.get("/clinic/reminder/1", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (302, 401, 403), f"Expected protected response; got {r.status_code}"
