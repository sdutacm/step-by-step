from datetime import datetime

from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    description: str | None = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    step_count: int = 0

    class Config:
        from_attributes = True


class GroupListItem(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    step_count: int = 0

    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GroupListItem]
