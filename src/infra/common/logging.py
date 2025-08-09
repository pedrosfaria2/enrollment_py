import json
import time
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from loguru import logger
from starlette.datastructures import UploadFile


class LogAPIRoute(APIRoute):
    """
    Custom route that logs detailed information about each request and response.
    """

    def __init__(
        self,
        *args,
        response_limit: int = 1000,
        body_limit: int = 1000,
        logger_instance=None,
        log_level: str = "INFO",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.RESPONSE_LIMIT = response_limit
        self.BODY_LIMIT = body_limit
        self.logger = logger_instance or logger
        self.log_level = log_level.upper()

    def get_route_handler(self) -> Callable:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            params, body = await self._extract_request_data(request)
            started = time.time()
            try:
                response = await original(request)
            except Exception as exc:
                await self._log_exception(request, exc, started, params, body)
                raise
            else:
                await self._after_route_handler(
                    request=request,
                    response=response,
                    before_time=started,
                    params=params,
                    body=body,
                )
                return response

        return handler

    async def _log_exception(
        self,
        request: Request,
        error: Exception,
        before_time: float,
        params: dict[str, Any],
        body: Any,
    ) -> None:
        duration = time.time() - before_time
        requester = await self._get_requestor_data(request)

        if isinstance(error, HTTPException):
            status_code = error.status_code
            response_text = str(getattr(error, "detail", error))
        elif isinstance(error, RequestValidationError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            response_text = "Validation error"
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_text = str(error)

        log_data = {
            "url": str(request.url),
            "method": request.method,
            "status_code": status_code,
            "duration": f"{duration:.3f}s",
            "parameters": params,
            "body": body if isinstance(body, str) else body,
            "response": response_text,
            "requester": requester,
        }
        self.logger.warning(log_data)

    async def _extract_request_data(self, request: Request) -> tuple[dict[str, Any], Any]:
        """
        Extracts request parameters and body.
        """
        try:
            params = dict(request.query_params)
            params.update(request.path_params)
            body = await self._get_request_body(request)
        except Exception as error:
            self.logger.error(f"Error processing request: {error}")
            params, body = {}, None
        return params, body

    async def _get_request_body(self, request: Request) -> Any:
        """
        Gets the request body, handling different content types.
        """
        try:
            content_type = request.headers.get("content-type", "").split(";")[0]
            if content_type in (
                "application/x-www-form-urlencoded",
                "multipart/form-data",
            ):
                return await self._process_form_data(request)
            elif content_type == "application/json":
                body = await request.json()
                return body
            else:
                body_bytes = await request.body()
                return body_bytes.decode("utf-8", errors="replace")
        except Exception as error:
            self.logger.warning(f"Error getting request body: {error}")
            return None

    @staticmethod
    async def _process_form_data(request: Request) -> dict[str, Any]:
        """
        Processes form data from the request.
        """
        form_data = await request.form()
        form_data_dict = {}
        for key, value in form_data.items():
            if isinstance(value, UploadFile):
                form_data_dict[key] = {
                    "filename": value.filename,
                    "content_type": value.content_type,
                    "file_size": value.size,
                }
            else:
                form_data_dict[key] = str(value)
        return form_data_dict

    async def _after_route_handler(
        self,
        request: Request,
        response: Response,
        before_time: float,
        params: dict[str, Any],
        body: Any,
    ):
        """
        Executes actions after route processing, logging request and response details.
        """
        try:
            duration = time.time() - before_time
            requester = await self._get_requestor_data(request)

            if isinstance(response, Response):
                if not hasattr(response, "headers") or response.headers is None:
                    response.headers = {}
                response.headers["X-Response-Time"] = f"{duration:.3f}s"

            log_response = self._get_log_response(response)
            self._log_request(request, response, duration, params, body, log_response, requester)

        except Exception as error:
            self.logger.error(f"Error in after_route_handler: {error}")

    def _get_log_response(self, response: Response) -> str:
        """
        Gets the response content to be logged.
        """
        if isinstance(response, Response):
            content_type = response.media_type or ""
            if "application/json" in content_type:
                try:
                    log_response = json.loads(response.body.decode("utf-8"))
                    return json.dumps(log_response)[: self.RESPONSE_LIMIT]
                except Exception as error:
                    self.logger.error(f"Error processing response: {error}")
                    return response.body.decode("utf-8", errors="replace")[: self.RESPONSE_LIMIT]
            else:
                return response.body.decode("utf-8", errors="replace")[: self.RESPONSE_LIMIT]
        elif isinstance(response, HTTPException):
            return str(response.detail)[: self.RESPONSE_LIMIT]
        else:
            return str(response)[: self.RESPONSE_LIMIT]

    def _log_request(
        self,
        request: Request,
        response: Response,
        duration: float,
        params: dict[str, Any],
        body: Any,
        log_response: str,
        requester: dict[str, Any],
    ):
        """
        Logs the request and response details.
        """
        log_data = {
            "url": str(request.url),
            "method": request.method,
            "status_code": response.status_code,
            "duration": f"{duration:.3f}s",
            "parameters": params,
            "body": body[: self.BODY_LIMIT] if isinstance(body, str) else body,
            "response": log_response[: self.RESPONSE_LIMIT],
            "requester": requester,
        }
        if self.log_level == "INFO":
            self.logger.info(log_data)
        elif self.log_level == "DEBUG":
            self.logger.debug(log_data)
        elif self.log_level == "WARNING":
            self.logger.warning(log_data)
        elif self.log_level == "ERROR":
            self.logger.error(log_data)
        else:
            self.logger.log(self.log_level, log_data)

    @staticmethod
    async def _get_requestor_data(request: Request) -> dict[str, Any]:
        """
        Gets information about the request sender from headers.
        """
        headers = request.headers
        return {
            "host": headers.get("host"),
            "client_host": request.client.host if request.client else None,
            "x_forwarded_for": headers.get("x-forwarded-for"),
            "user_agent": headers.get("user-agent"),
            "referer": headers.get("referer"),
            "content_type": headers.get("content-type", headers.get("accept")),
            "content_length": headers.get("content-length"),
            "origin": headers.get("origin"),
            "connection": headers.get("connection"),
        }
