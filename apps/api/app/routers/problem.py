from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models.problem import Problem
from db.session import get_db
from schemas.solution import ProblemSimple

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("")
def get_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(Problem.id)).scalar()
    offset = (page - 1) * page_size

    problems = (
        db.query(Problem)
        .order_by(Problem.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = [
        ProblemSimple(
            id=p.id,
            problem_id=p.problem_id,
            source=p.source,
            title=p.title,
            order=0,
        )
        for p in problems
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
