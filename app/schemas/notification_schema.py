from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    id: int
    title: str
    content: str
    biz_type: str
    biz_id: int | None = None
    read_status: int
    created_at: datetime
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationBatchRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1, max_length=100)


class NotificationProcessedResult(BaseModel):
    processed_count: int