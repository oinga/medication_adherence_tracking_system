# tests/test_meds_and_adherence.py
import logging
logger = logging.getLogger(__name__)

def test_medications_requires_auth_or_patient_session(client):
    logger.info("GET /medications (unauthenticated) -> expect redirect/forbidden")
    r = client.get("/medications", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (302, 401, 403), f"Expected protected response; got {r.status_code}"

def test_dose_history_requires_patient_session(client):
    logger.info("GET /dose-history (unauthenticated) -> expect redirect/forbidden")
    r = client.get("/dose-history", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (302, 401, 403), f"Expected protected response; got {r.status_code}"

def test_request_callback_requires_patient_session(client):
    logger.info("GET /request-callback (unauthenticated) -> expect redirect/forbidden")
    r = client.get("/request-callback", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (302, 401, 403), f"Expected protected response; got {r.status_code}"

def test_mutating_routes_are_not_open_to_get(client):
    for path in ("/medications/miss/1", "/medications/reminder/1"):
        logger.info("GET %s -> expect 405 or protected redirect (POST-only route)", path)
        r = client.get(path, follow_redirects=False)
        logger.info("Received status=%s", r.status_code)
        assert r.status_code in (405, 302, 401, 403), f"{path} should not allow GET; got {r.status_code}"
