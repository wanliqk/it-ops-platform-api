from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from app.utils.timezone import format_date, format_datetime


def success(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": _normalize_response_data(data)}


def fail(code: int = 40000, message: str = "操作失败", data: Any = None) -> dict[str, Any]:
    return {"code": code, "message": message, "data": _normalize_response_data(data)}


def success_response(data: Any = None) -> dict[str, Any]:
    return {
        "code": 200,
        "message": "success",
        "data": _normalize_response_data(data if data is not None else {}),
    }


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


def _normalize_response_data(data: Any) -> Any:
    if isinstance(data, datetime):
        return format_datetime(data)
    if isinstance(data, date):
        return format_date(data)
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, dict):
        return {key: _normalize_response_data(value) for key, value in data.items()}
    if isinstance(data, list | tuple | set):
        return [_normalize_response_data(item) for item in data]
    return data
