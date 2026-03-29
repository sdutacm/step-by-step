from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.models.problem import Problem
from db.session import get_db
from schemas.solution import ProblemSimple

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("")
def get_problems(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    title: str | None = Query(None),
    source: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Problem)

    if title:
        query = query.filter(Problem.title.contains(title))
    if source:
        query = query.filter(Problem.source == source)

    total = query.count()
    offset = (page - 1) * page_size

    problems = query.order_by(Problem.id.desc()).offset(offset).limit(page_size).all()

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
