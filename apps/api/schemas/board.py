from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class BoardVisibility(str, Enum):
    PUBLIC = "public"
    GROUP_MEMBER = "group_member"
    BOARD_USER = "board_user"


class BoardBase(BaseModel):
    name: str
    description: str | None = None
    visibility: BoardVisibility = BoardVisibility.BOARD_USER


class BoardCreate(BoardBase):
    step_id: int


class BoardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: BoardVisibility | None = None
    step_id: int | None = None


class BoardResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    visibility: BoardVisibility
    group_id: int
    group_name: str | None = None
    created_by: int
    creator_username: str
    created_at: datetime
    updated_at: datetime
    step_id: int
    step_title: str
    member_count: int = 0

    class Config:
        from_attributes = True


class BoardListItem(BaseModel):
    id: int
    name: str
    description: str | None = None
    visibility: BoardVisibility
    group_id: int
    created_by: int
    creator_username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BoardListItem]


class BoardUserResponse(BaseModel):
    id: int
    board_id: int
    user_id: int
    username: str
    nickname: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class BoardUserListResponse(BaseModel):
    total: int
    items: list[BoardUserResponse]


class ProblemProgress(BaseModel):
    problem_id: int
    oj_problem_id: str
    title: str
    order: int = 0
    specialty: str | None = None
    topic: str | None = None
    ac_time: datetime | None = None


class StepProgress(BaseModel):
    step_id: int
    step_title: str
    total_problems: int
    solved_problems: int
    progress_percent: float
    status: str
    problems: list[ProblemProgress]


class UserBoardProgress(BaseModel):
    user_id: int
    username: str
    nickname: str | None = None
    solved_problems: int
    total_problems: int
    progress_percent: float
    status: str
    problems: list[ProblemProgress]


class BoardProgressResponse(BaseModel):
    board_id: int
    board_name: str
    step_id: int
    step_title: str
    group_id: int
    users: list[UserBoardProgress]
