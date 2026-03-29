from datetime import datetime

from pydantic import BaseModel

from schemas.solution import ProblemSimple


class StepBase(BaseModel):
    title: str
    description: str | None = None


class StepCreate(StepBase):
    group_id: int | None = None


class StepUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class StepProblemItem(BaseModel):
    problem_id: int
    order: int = 0
    specialty: str | None = None
    topic: str | None = None


class StepProblemAddRequest(BaseModel):
    problems: list[StepProblemItem]


class StepResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    creator_id: int
    creator_username: str
    group_id: int | None = None
    group_name: str | None = None
    created_at: datetime
    updated_at: datetime
    problems: list[ProblemSimple] = []
    problem_count: int = 0

    class Config:
        from_attributes = True


class StepListItem(BaseModel):
    id: int
    title: str
    description: str | None = None
    creator_id: int
    creator_username: str
    group_id: int | None = None
    group_name: str | None = None
    created_at: datetime
    updated_at: datetime
    problem_count: int = 0

    class Config:
        from_attributes = True


class StepListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[StepListItem]
