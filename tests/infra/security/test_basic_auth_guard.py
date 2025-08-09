import base64

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasicCredentials
from starlette.testclient import TestClient

from infra.security.basic_auth import BasicAuthGuard


def _creds(u: str, p: str) -> HTTPBasicCredentials:
    return HTTPBasicCredentials(username=u, password=p)


def test_guard_returns_username_on_success():
    guard = BasicAuthGuard("user", "pass")
    assert guard(_creds("user", "pass")) == "user"


def test_guard_raises_on_wrong_username():
    guard = BasicAuthGuard("user", "pass")
    with pytest.raises(HTTPException) as exc:
        guard(_creds("wrong", "pass"))
    err = exc.value
    assert err.status_code == 401
    assert err.detail == "Invalid authentication credentials"
    assert err.headers.get("WWW-Authenticate") == 'Basic realm="EnrollmentAPI"'  # type: ignore


def test_guard_raises_on_wrong_password():
    guard = BasicAuthGuard("user", "pass")
    with pytest.raises(HTTPException) as exc:
        guard(_creds("user", "nope"))
    assert exc.value.status_code == 401


def test_guard_raises_on_missing_credentials_none():
    guard = BasicAuthGuard("user", "pass")
    with pytest.raises(HTTPException) as exc:
        guard(None)  # type: ignore[arg-type]
    assert exc.value.status_code == 401


def test_guard_respects_custom_realm_header():
    guard = BasicAuthGuard("user", "pass", realm="MyRealm")
    with pytest.raises(HTTPException) as exc:
        guard(_creds("user", "bad"))
    assert exc.value.headers.get("WWW-Authenticate") == 'Basic realm="MyRealm"'  # type: ignore


def _client(username="user", password="pass") -> TestClient:
    app = FastAPI()
    auth = BasicAuthGuard(username, password)

    @app.get("/protected", dependencies=[Depends(auth)])
    def protected():
        return {"ok": True}

    @app.get("/public")
    def public():
        return {"ok": "public"}

    return TestClient(app)


def _basic_auth_header(u: str, p: str) -> dict[str, str]:
    token = base64.b64encode(f"{u}:{p}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_integration_protected_route_allows_valid_creds():
    client = _client()
    r = client.get("/protected", headers=_basic_auth_header("user", "pass"))
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_integration_protected_route_rejects_no_header():
    client = _client()
    r = client.get("/protected")
    assert r.status_code == 401
    assert r.headers.get("WWW-Authenticate", r.headers.get("www-authenticate")) == 'Basic realm="EnrollmentAPI"'


def test_integration_protected_route_rejects_bad_creds():
    client = _client()
    r = client.get("/protected", headers=_basic_auth_header("user", "nope"))
    assert r.status_code == 401


def test_integration_public_route_is_open():
    client = _client()
    r = client.get("/public")
    assert r.status_code == 200
    assert r.json() == {"ok": "public"}
