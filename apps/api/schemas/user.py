from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class SourceUserResponse(BaseModel):
    id: int
    source: str

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    nickname: str | None = None
    avatar_url: str | None = None
    source_users: list[SourceUserResponse] = []

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str
