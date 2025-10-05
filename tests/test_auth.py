# tests/test_auth.py
import logging
logger = logging.getLogger(__name__)

def test_patient_login_page_renders(client):
    logger.info("GET / (patient login) -> expect 200 and CSRF field present")
    r = client.get("/")
    logger.info("Received status=%s, content-type=%s", r.status_code, r.headers.get("Content-Type"))
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert b'name="csrf_token"' in r.data, "Expected CSRF token on patient login form"

def test_clinic_login_page_renders(client):
    logger.info("GET /clinic_login -> expect 200 and username/password fields + CSRF")
    r = client.get("/clinic_login")
    logger.info("Received status=%s", r.status_code)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert b'name="csrf_token"' in r.data, "Expected CSRF token on clinic login form"
    assert b'name="username"' in r.data, "Expected username field"
    assert b'name="password"' in r.data, "Expected password field"

def test_protected_pages_redirect_when_not_logged_in(client):
    protected = ["/clinic_dashboard", "/medications", "/dose-history", "/request-callback"]
    for path in protected:
        logger.info("GET %s (unauthenticated) -> expect redirect/forbidden", path)
        r = client.get(path, follow_redirects=False)
        logger.info("Received status=%s", r.status_code)
        assert r.status_code in (302, 401, 403), f"{path} should be protected; got {r.status_code}"

def test_logout_redirects_when_not_logged_in(client):
    logger.info("GET /logout (unauthenticated) -> expect redirect to a safe page")
    r = client.get("/logout", follow_redirects=False)
    logger.info("Received status=%s", r.status_code)
    assert r.status_code in (302, 303), f"Expected redirect; got {r.status_code}"
