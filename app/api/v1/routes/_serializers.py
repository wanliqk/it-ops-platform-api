from decimal import Decimal
from typing import Any


def obj_dict(obj: Any, fields: list[str]) -> dict[str, Any]:
    return {field: _value(getattr(obj, field)) for field in fields}


def user_dict(user: Any) -> dict[str, Any]:
    return obj_dict(
        user,
        [
            "id",
            "username",
            "real_name",
            "role",
            "department",
            "phone",
            "email",
            "status",
            "created_at",
            "updated_at",
        ],
    )


def category_dict(category: Any) -> dict[str, Any]:
    return obj_dict(
        category,
        [
            "id",
            "category_name",
            "category_code",
            "description",
            "status",
            "created_at",
            "updated_at",
        ],
    )


def asset_dict(asset: Any) -> dict[str, Any]:
    data = obj_dict(
        asset,
        [
            "id",
            "asset_no",
            "asset_name",
            "category_id",
            "brand",
            "model",
            "serial_no",
            "user_id",
            "department",
            "location",
            "status",
            "purchase_date",
            "warranty_expire_date",
            "remark",
            "created_at",
            "updated_at",
        ],
    )
    data["category_name"] = asset.category.category_name if asset.category else None
    data["user_name"] = asset.user.real_name if asset.user else None
    return data


def ticket_dict(ticket: Any) -> dict[str, Any]:
    data = obj_dict(
        ticket,
        [
            "id",
            "ticket_no",
            "title",
            "description",
            "fault_type",
            "priority",
            "status",
            "reporter_id",
            "handler_id",
            "asset_id",
            "result",
            "created_at",
            "assigned_at",
            "started_at",
            "completed_at",
            "updated_at",
        ],
    )
    data["reporter_name"] = ticket.reporter.real_name if ticket.reporter else None
    data["handler_name"] = ticket.handler.real_name if ticket.handler else None
    data["asset_no"] = ticket.asset.asset_no if ticket.asset else None
    data["asset_name"] = ticket.asset.asset_name if ticket.asset else None
    return data


def ticket_record_dict(record: Any) -> dict[str, Any]:
    data = obj_dict(
        record,
        [
            "id",
            "ticket_id",
            "operator_id",
            "from_status",
            "to_status",
            "action",
            "remark",
            "created_at",
        ],
    )
    data["operator_name"] = record.operator.real_name if record.operator else None
    return data


def repair_record_dict(record: Any) -> dict[str, Any]:
    data = obj_dict(
        record,
        [
            "id",
            "ticket_id",
            "asset_id",
            "repair_user_id",
            "fault_reason",
            "repair_method",
            "repair_result",
            "repair_cost",
            "repaired_at",
            "created_at",
        ],
    )
    data["ticket_no"] = record.ticket.ticket_no if record.ticket else None
    data["ticket_title"] = record.ticket.title if record.ticket else None
    data["asset_no"] = record.asset.asset_no if record.asset else None
    data["asset_name"] = record.asset.asset_name if record.asset else None
    data["repair_user_name"] = record.repair_user.real_name if record.repair_user else None
    return data


def operation_log_dict(log: Any) -> dict[str, Any]:
    data = obj_dict(
        log,
        [
            "id",
            "user_id",
            "module_name",
            "operation_type",
            "business_id",
            "request_method",
            "request_url",
            "request_ip",
            "operation_result",
            "error_message",
            "created_at",
        ],
    )
    data["username"] = log.user.username if log.user else None
    data["real_name"] = log.user.real_name if log.user else None
    return data


def _value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value
