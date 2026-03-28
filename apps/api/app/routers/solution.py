from db.models.problem import Problem
from db.models.solution import Solution
from db.session import get_db
from fastapi import APIRouter, Depends, Query
from schemas.solution import PaginatedSolutionsResponse, SolutionResponse
from sqlalchemy.orm import Session, joinedload

router = APIRouter(prefix="/api/solutions", tags=["solutions"])


@router.get("/", response_model=PaginatedSolutionsResponse)
def get_solutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(Solution).count()
    offset = (page - 1) * page_size

    solutions = (
        db.query(Solution)
        .options(joinedload(Solution.problem))
        .order_by(Solution.submitted_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        SolutionResponse(
            id=s.id,
            username=s.username,
            nickname=s.nickname,
            source=s.source,
            result=s.result,
            language=s.language,
            submitted_at=s.submitted_at,
            solution_id=s.solution_id,
            problem_id=s.problem_id,
            oj_problem_id=s.problem.problem_id if s.problem else None,
            problem_title=s.problem.title if s.problem else None,
        )
        for s in solutions
    ]

    return PaginatedSolutionsResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
