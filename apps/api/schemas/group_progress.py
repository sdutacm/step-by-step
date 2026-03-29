from datetime import datetime

from pydantic import BaseModel


class GroupProblemProgress(BaseModel):
    problem_id: int
    oj_problem_id: str
    title: str
    ac_time: datetime
    order: int = 0


class GroupStepProgress(BaseModel):
    step_id: int
    step_title: str
    total_problems: int
    solved_problems: int
    progress_percent: float
    problems: list[GroupProblemProgress]


class GroupUserProgress(BaseModel):
    user_id: int
    username: str
    nickname: str | None = None
    steps: list[GroupStepProgress]
    total_solved: int


class GroupProgressResponse(BaseModel):
    group_id: int
    group_name: str
    members: list[GroupUserProgress]
