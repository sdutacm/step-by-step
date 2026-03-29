from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    avatar_url: str | None = None
    is_super_admin: bool

    model_config = {"from_attributes": True}


class UserListItem(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    avatar_url: str | None = None
    is_super_admin: bool

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserListItem]


class UserSuperAdminUpdate(BaseModel):
    is_super_admin: bool
