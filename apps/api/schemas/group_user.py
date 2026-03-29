from datetime import datetime

from pydantic import BaseModel

from db.models.group_user import GroupRole


class GroupMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    nickname: str | None = None
    role: GroupRole
    joined_at: datetime

    class Config:
        from_attributes = True


class GroupMemberAddRequest(BaseModel):
    username: str


class GroupMemberUpdateRequest(BaseModel):
    role: GroupRole


class GroupMemberListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[GroupMemberResponse]
