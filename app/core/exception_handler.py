from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import fail
from app.core.exceptions import AppException


def _cors_json_response(status_code: int, content: dict) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


def register_exception_handlers(app: FastAPI) -> None:

    # ✅ 业务异常（统一返回200）
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        response = fail(
            code=exc.code,
            message=exc.message,
            data=exc.data
        )
        return _cors_json_response(
            status_code=200,
            content=response.model_dump()
        )

    # ✅ FastAPI / Depends / Header 等抛出的 HTTP 异常
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        response = fail(
            code=exc.status_code,
            message=exc.detail,
            data=None
        )
        return _cors_json_response(
            status_code=exc.status_code,
            content=response.model_dump()
        )

    # ✅ 参数校验异常
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        response = fail(
            code=400,
            message="invalid request",
            data=exc.errors()
        )
        return _cors_json_response(
            status_code=400,
            content=response.model_dump()
        )

    # ✅ 未捕获异常（系统错误）
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        print("Unhandled Exception:", str(exc))

        response = fail(
            code=500,
            message="internal server error",
            data=None
        )
        return _cors_json_response(
            status_code=500,
            content=response.model_dump()
        )