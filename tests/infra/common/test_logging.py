import json

import pytest
from fastapi import Body, FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.routing import APIRouter
from pydantic import BaseModel
from starlette.testclient import TestClient

from infra.common.logging import LogAPIRoute


class _MemLogger:
    def __init__(self):
        self.records: list = []

    def info(self, payload):
        self.records.append(payload)

    def debug(self, payload):
        self.records.append(payload)

    def warning(self, payload):
        self.records.append(payload)

    def error(self, payload):
        self.records.append(payload)

    def log(self, *_args, **_kwargs):
        self.records.append(("custom", _args, _kwargs))


class _RouteBase(LogAPIRoute):
    _logger = _MemLogger()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger_instance", self._logger)
        super().__init__(*args, **kwargs)


class _RouteInfo(_RouteBase):
    pass


class _RouteDebug(_RouteBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger_instance", self._logger)
        kwargs.setdefault("log_level", "DEBUG")
        super().__init__(*args, **kwargs)


class _RouteWarning(_RouteBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger_instance", self._logger)
        kwargs.setdefault("log_level", "WARNING")
        super().__init__(*args, **kwargs)


class _RouteError(_RouteBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger_instance", self._logger)
        kwargs.setdefault("log_level", "ERROR")
        super().__init__(*args, **kwargs)


class _RouteCustom(_RouteBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger_instance", self._logger)
        kwargs.setdefault("log_level", "NOTICE")
        super().__init__(*args, **kwargs)


class _RouteTrunc(_RouteBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("logger_instance", self._logger)
        kwargs.setdefault("response_limit", 5)
        kwargs.setdefault("body_limit", 5)
        super().__init__(*args, **kwargs)


@pytest.fixture
def client_and_logger():
    app = FastAPI()
    router = APIRouter(route_class=_RouteInfo)

    class Item(BaseModel):
        x: int
        y: str

    @router.post("/json")
    def json_ep(item: Item):
        return {"ok": True, "sum": item.x, "y": item.y}

    @router.post("/form")
    def form_ep(a: str = Form(...), b: str = Form(...)):
        return {"a": a, "b": b}

    @router.post("/text")
    def text_ep(body: str = Body(..., media_type="text/plain")):
        return {"len": len(body)}

    @router.post("/file")
    def file_ep(file: UploadFile = File(...)):  # noqa: B008
        return {"fn": file.filename, "ct": file.content_type}

    @router.get("/boom")
    def boom():
        raise HTTPException(status_code=418, detail="teapot")

    @router.get("/raw-json-bad")
    def raw_json_bad():
        return Response(content="not-json", media_type="application/json")

    @router.get("/raw-text")
    def raw_text():
        return Response(content="hello", media_type="text/plain")

    app.include_router(router)
    return TestClient(app), _RouteInfo._logger


def test_json_request_logs_and_header(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.post("/json", json={"x": 7, "y": "abc"})
    assert r.status_code == 200 and "X-Response-Time" in r.headers
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 200 and rec["method"] == "POST" and rec["parameters"] == {}
    body = rec["body"]
    assert isinstance(body, dict) and body["x"] == 7 and body["y"] == "abc"
    resp = json.loads(rec["response"])
    assert resp["ok"] is True and resp["sum"] == 7


def test_urlencoded_form_is_captured(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.post("/form", data={"a": "1", "b": "2"})
    assert r.status_code == 200
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 200 and rec["body"] == {"a": "1", "b": "2"}


def test_plain_text_is_captured_as_string(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.post("/text", data="hello world", headers={"content-type": "text/plain"})
    assert r.status_code == 200
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 200 and rec["body"] == "hello world"


def test_file_upload_branch_in_form_processing(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    files = {"file": ("hello.txt", b"abc", "text/plain")}
    r = client.post("/file", files=files)
    assert r.status_code == 200
    rec = next(x for x in log.records if isinstance(x, dict))
    f = rec["body"]["file"]
    assert f["filename"] == "hello.txt" and f["content_type"] == "text/plain" and f["file_size"] >= 0


def test_http_exception_is_logged_and_raised(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.get("/boom")
    assert r.status_code == 418
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 418 and "teapot" in rec["response"]


def test_pydantic_validation_error_is_mapped_and_logged(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.post("/json", json={"x": "NaN", "y": 1})
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 400 and "Validation error" in rec["response"]


def test_invalid_json_triggers_400_and_warning(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.post("/json", data="{not valid json", headers={"content-type": "application/json"})
    assert r.status_code == status.HTTP_400_BAD_REQUEST
    assert any(isinstance(x, dict) and x.get("status_code") == 400 for x in log.records)


def test_generic_exception_maps_to_500_and_is_logged():
    app = FastAPI()
    router = APIRouter(route_class=_RouteInfo)

    @router.get("/oops")
    def oops():
        raise RuntimeError("boom")

    app.include_router(router)
    client = TestClient(app)
    _RouteInfo._logger.records.clear()
    r = client.get("/oops")
    assert r.status_code == 500
    rec = next(x for x in _RouteInfo._logger.records if isinstance(x, dict))
    assert rec["status_code"] == 500 and "Internal server error" in rec["response"]


def test_after_route_handler_error_logging(monkeypatch, client_and_logger):
    client, log = client_and_logger
    log.records.clear()

    def _explode(*_a, **_k):
        raise RuntimeError("whoops")

    monkeypatch.setattr(_RouteInfo, "_get_requestor_data", staticmethod(_explode))
    r = client.post("/json", json={"x": 1, "y": "a"})
    assert r.status_code == 200
    assert any(isinstance(x, str) and "Error in after_route_handler" in x for x in log.records)


def test_extract_request_data_outer_exception(monkeypatch):
    app = FastAPI()
    router = APIRouter(route_class=_RouteInfo)

    @router.post("/txt")
    def txt(body: str = Body(..., media_type="text/plain")):
        return {"ok": True}

    def boom(self, request):
        raise RuntimeError("explode in extractor")

    monkeypatch.setattr(_RouteInfo, "_get_request_body", boom, raising=True)

    app.include_router(router)
    client = TestClient(app)
    _RouteInfo._logger.records.clear()
    r = client.post("/txt", data="x", headers={"content-type": "text/plain"})  # type: ignore
    assert r.status_code == 200
    assert any(isinstance(x, str) and "Error processing request:" in x for x in _RouteInfo._logger.records)


def test_get_log_response_json_error_fallback(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.get("/raw-json-bad")
    assert r.status_code == 200
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 200 and rec["response"] == "not-json"


def test_get_log_response_plain_text_branch(client_and_logger):
    client, log = client_and_logger
    log.records.clear()
    r = client.get("/raw-text")
    assert r.status_code == 200
    rec = next(x for x in log.records if isinstance(x, dict))
    assert rec["status_code"] == 200 and rec["response"] == "hello"


def test_log_levels_debug_warning_error_and_custom():
    app = FastAPI()
    dbg = APIRouter(route_class=_RouteDebug)
    wrn = APIRouter(route_class=_RouteWarning)
    err = APIRouter(route_class=_RouteError)
    cst = APIRouter(route_class=_RouteCustom)

    @dbg.get("/dbg")
    def _dbg():
        return {"ok": True}

    @wrn.get("/wrn")
    def _wrn():
        return {"ok": True}

    @err.get("/err")
    def _err():
        return {"ok": True}

    @cst.get("/cst")
    def _cst():
        return {"ok": True}

    app.include_router(dbg)
    app.include_router(wrn)
    app.include_router(err)
    app.include_router(cst)
    client = TestClient(app)
    _RouteDebug._logger.records.clear()
    _RouteWarning._logger.records.clear()
    _RouteError._logger.records.clear()
    _RouteCustom._logger.records.clear()

    assert client.get("/dbg").status_code == 200
    assert client.get("/wrn").status_code == 200
    assert client.get("/err").status_code == 200
    assert client.get("/cst").status_code == 200

    assert any(isinstance(x, dict) for x in _RouteDebug._logger.records)
    assert any(isinstance(x, dict) for x in _RouteWarning._logger.records)
    assert any(isinstance(x, dict) for x in _RouteError._logger.records)
    assert any(isinstance(x, tuple) and x[0] == "custom" for x in _RouteCustom._logger.records)


def test_truncation_of_body_and_response():
    app = FastAPI()
    router = APIRouter(route_class=_RouteTrunc)

    @router.post("/echo")
    def echo(body: str = Body(..., media_type="text/plain")):
        return Response(content="X" * 20, media_type="text/plain")

    app.include_router(router)
    client = TestClient(app)
    _RouteTrunc._logger.records.clear()
    r = client.post("/echo", data="Y" * 20, headers={"content-type": "text/plain"})  # type: ignore
    assert r.status_code == 200
    rec = next(x for x in _RouteTrunc._logger.records if isinstance(x, dict))
    assert rec["body"] == "Y" * 5
    assert rec["response"] == "X" * 5
