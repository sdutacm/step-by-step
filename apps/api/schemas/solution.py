from datetime import datetime

from pydantic import BaseModel

from schemas.language import LanguageEnum
from schemas.result import ResultEnum


class SolutionResponse(BaseModel):
    id: int
    username: str
    nickname: str | None = None
    source: str
    result: ResultEnum
    language: LanguageEnum
    submitted_at: datetime
    solution_id: int
    problem_id: int | None = None
    oj_problem_id: str | None = None
    problem_title: str | None = None

    class Config:
        from_attributes = True


class PaginatedSolutionsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SolutionResponse]


class ProblemSimple(BaseModel):
    id: int
    problem_id: str
    source: str
    title: str
    order: int = 0

    class Config:
        from_attributes = True
