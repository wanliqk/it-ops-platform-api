from typing import Any


def success_response(data: Any = None) -> dict[str, Any]:
    return {"code": 200, "message": "success", "data": data if data is not None else {}}


def error_response(message: str, code: int = 400) -> dict[str, Any]:
    return {"code": code, "message": message, "data": None}


class MobileAPIException(Exception):
    def __init__(self, message: str, status_code: int = 400, code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code or status_code
