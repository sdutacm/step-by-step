from datetime import datetime

from pydantic import BaseModel

from schemas.solution import ProblemSimple


class StepBase(BaseModel):
    title: str
    description: str | None = None


class StepCreate(StepBase):
    pass


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


class StepProblemReorderRequest(BaseModel):
    problem_ids: list[int]


class StepResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    creator_id: int
    creator_username: str
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
