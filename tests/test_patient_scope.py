# tests/test_patient_scope.py
import logging
logger = logging.getLogger(__name__)

def test_take_route_not_accessible_without_session(client):
    logger.info("GET /medications/take/1 (unauthenticated) -> expect redirect/forbidden")
    r = client.get("/medications/take/1", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (302, 401, 403), f"Expected protected response; got {r.status_code}"

def test_static_is_accessible_without_auth(client):
    logger.info("GET /static/styles.css -> expect 200 if file exists, else 404")
    r = client.get("/static/styles.css")
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (200, 404), f"Expected 200/404; got {r.status_code}"
