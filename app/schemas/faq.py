from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.faq import FaqCategory


class FaqBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: FaqCategory
    summary: str | None = Field(default=None, max_length=255)
    content: str = Field(min_length=1)
    sort_order: int = 0
    status: int = 1


class FaqCreate(FaqBase):
    pass


class FaqUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: FaqCategory | None = None
    summary: str | None = Field(default=None, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    sort_order: int | None = None
    status: int | None = None


class FaqStatusUpdate(BaseModel):
    status: int


class FaqRead(FaqBase):
    id: int
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
