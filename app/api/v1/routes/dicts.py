from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.core.responses import success
from app.models import User

router = APIRouter()


@router.get("")
def dicts(_: Annotated[User, Depends(get_current_user)]) -> dict:
    return success(
        {
            "roles": [
                {"label": "管理员", "value": "admin"},
                {"label": "IT运维人员", "value": "it_staff"},
                {"label": "普通员工", "value": "employee"},
            ],
            "ticket_status": [
                {"label": "待受理", "value": "pending"},
                {"label": "已派单", "value": "assigned"},
                {"label": "处理中", "value": "processing"},
                {"label": "已完成", "value": "completed"},
                {"label": "已取消", "value": "cancelled"},
            ],
            "ticket_priority": [
                {"label": "低", "value": "low"},
                {"label": "普通", "value": "normal"},
                {"label": "高", "value": "high"},
                {"label": "紧急", "value": "urgent"},
            ],
            "fault_type": [
                {"label": "硬件故障", "value": "hardware"},
                {"label": "软件故障", "value": "software"},
                {"label": "网络故障", "value": "network"},
                {"label": "打印机故障", "value": "printer"},
                {"label": "账号权限问题", "value": "account"},
                {"label": "其他", "value": "other"},
            ],
            "asset_status": [
                {"label": "在用", "value": "in_use"},
                {"label": "闲置", "value": "idle"},
                {"label": "维修中", "value": "repairing"},
                {"label": "已报废", "value": "scrapped"},
            ],
        }
    )
