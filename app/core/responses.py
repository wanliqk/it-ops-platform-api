from typing import Any


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def fail(code: int = 40000, message: str = "操作失败", data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": data}


def success_response(data: Any = None) -> dict[str, Any]:
    return {"code": 200, "message": "success", "data": data if data is not None else {}}


def error_response(message: str, code: int = 400) -> dict[str, Any]:
    return {"code": code, "message": message, "data": None}


class MobileAPIException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code or status_code


class APIException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int = 40000) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
