from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.routers.auth import get_current_user
from db.models.group import Group
from db.models.group_user import GroupRole, GroupUser
from db.models.problem import Problem
from db.models.step import Step
from db.models.step_problem import StepProblem
from db.models.user import User
from db.session import get_db
from schemas.step import (
    ProblemSimple,
    StepCreate,
    StepListItem,
    StepListResponse,
    StepProblemAddRequest,
    StepResponse,
    StepUpdate,
)

router = APIRouter(prefix="/api/steps", tags=["steps"])


@router.post("", response_model=StepResponse, status_code=status.HTTP_201_CREATED)
def create_step(
    step_data: StepCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Create step: user={current_user.username}, title={step_data.title}")
    group = None
    if step_data.group_id is not None:
        group = db.query(Group).filter(Group.id == step_data.group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        gu = (
            db.query(GroupUser)
            .filter(
                GroupUser.group_id == step_data.group_id,
                GroupUser.user_id == current_user.id,
            )
            .first()
        )
        if not gu:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group",
            )
    step = Step(
        title=step_data.title,
        description=step_data.description,
        created_by=current_user.id,
        group_id=step_data.group_id,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    logger.success(f"Step created: id={step.id}, title={step.title}")
    return StepResponse(
        id=step.id,
        title=step.title,
        description=step.description,
        creator_id=step.created_by,
        creator_username=current_user.username,
        group_id=step.group_id,
        group_name=group.name if group else None,
        created_at=step.created_at,
        updated_at=step.updated_at,
        problems=[],
        problem_count=0,
    )


@router.get("", response_model=StepListResponse)
def list_steps(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    logger.debug(f"List steps: page={page}, page_size={page_size}")
    total = db.query(func.count(Step.id)).scalar()
    steps = (
        db.query(Step)
        .options(joinedload(Step.step_problems), joinedload(Step.group))
        .order_by(Step.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        StepListItem(
            id=step.id,
            title=step.title,
            description=step.description,
            creator_id=step.created_by,
            creator_username=step.creator.username if step.creator else "",
            group_id=step.group_id,
            group_name=step.group.name if step.group else None,
            created_at=step.created_at,
            updated_at=step.updated_at,
            problem_count=len(step.step_problems),
        )
        for step in steps
    ]
    logger.debug(f"List steps: total={total}, returned={len(items)}")
    return StepListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{step_id}", response_model=StepResponse)
def get_step(
    step_id: int,
    db: Session = Depends(get_db),
):
    logger.debug(f"Get step: id={step_id}")
    step = (
        db.query(Step)
        .options(joinedload(Step.step_problems).joinedload(StepProblem.problem))
        .filter(Step.id == step_id)
        .first()
    )
    if not step:
        logger.warning(f"Step {step_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    problems = [
        ProblemSimple(
            id=sp.problem.id,
            problem_id=sp.problem.problem_id,
            source=sp.problem.source,
            title=sp.problem.title,
            order=sp.order,
            specialty=sp.specialty,
            topic=sp.topic,
        )
        for sp in sorted(step.step_problems, key=lambda x: x.order)
    ]
    return StepResponse(
        id=step.id,
        title=step.title,
        description=step.description,
        creator_id=step.created_by,
        creator_username=step.creator.username if step.creator else "",
        group_id=step.group_id,
        group_name=step.group.name if step.group else None,
        created_at=step.created_at,
        updated_at=step.updated_at,
        problems=problems,
        problem_count=len(step.step_problems),
    )


@router.put("/{step_id}", response_model=StepResponse)
def update_step(
    step_id: int,
    update_data: StepUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Update step: id={step_id}, user={current_user.username}")
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        logger.warning(f"Step {step_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    if step.created_by != current_user.id:
        logger.warning(
            f"Step {step_id}: user {current_user.username} is not the creator"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this step",
        )
    if update_data.title is not None:
        step.title = update_data.title
    if update_data.description is not None:
        step.description = update_data.description
    db.commit()
    db.refresh(step)
    logger.success(f"Step {step_id} updated")
    return StepResponse(
        id=step.id,
        title=step.title,
        description=step.description,
        creator_id=step.created_by,
        creator_username=step.creator.username if step.creator else "",
        group_id=step.group_id,
        group_name=step.group.name if step.group else None,
        created_at=step.created_at,
        updated_at=step.updated_at,
        problems=[],
        problem_count=len(step.step_problems),
    )


@router.delete("/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_step(
    step_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Delete step: id={step_id}, user={current_user.username}")
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        logger.warning(f"Step {step_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    if step.created_by != current_user.id:
        logger.warning(
            f"Step {step_id}: user {current_user.username} is not the creator"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this step",
        )
    db.delete(step)
    db.commit()
    logger.success(f"Step {step_id} deleted")


@router.post(
    "/{step_id}/problems",
    response_model=StepResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_problems_to_step(
    step_id: int,
    request: StepProblemAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Add problems to step: step_id={step_id}, user={current_user.username}, problems={len(request.problems)}"
    )
    step = (
        db.query(Step)
        .options(joinedload(Step.step_problems).joinedload(StepProblem.problem))
        .filter(Step.id == step_id)
        .first()
    )
    if not step:
        logger.warning(f"Step {step_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    if step.created_by != current_user.id:
        logger.warning(
            f"Step {step_id}: user {current_user.username} is not the creator"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this step",
        )
    for item in request.problems:
        problem = db.query(Problem).filter(Problem.id == item.problem_id).first()
        if not problem:
            logger.warning(f"Problem {item.problem_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Problem {item.problem_id} not found",
            )
        existing = (
            db.query(StepProblem)
            .filter(
                StepProblem.step_id == step_id,
                StepProblem.problem_id == item.problem_id,
            )
            .first()
        )
        if existing:
            logger.warning(f"Problem {item.problem_id} already in step {step_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Problem {item.problem_id} already in this step",
            )
        step_problem = StepProblem(
            step_id=step_id,
            problem_id=item.problem_id,
            order=item.order,
            specialty=item.specialty,
            topic=item.topic,
        )
        db.add(step_problem)
    db.commit()
    db.refresh(step)
    logger.success(f"Added {len(request.problems)} problems to step {step_id}")
    step = (
        db.query(Step)
        .options(joinedload(Step.step_problems).joinedload(StepProblem.problem))
        .filter(Step.id == step_id)
        .first()
    )
    problems = [
        ProblemSimple(
            id=sp.problem.id,
            problem_id=sp.problem.problem_id,
            source=sp.problem.source,
            title=sp.problem.title,
            order=sp.order,
            specialty=sp.specialty,
            topic=sp.topic,
        )
        for sp in sorted(step.step_problems, key=lambda x: x.order)
    ]
    return StepResponse(
        id=step.id,
        title=step.title,
        description=step.description,
        creator_id=step.created_by,
        creator_username=step.creator.username if step.creator else "",
        group_id=step.group_id,
        group_name=step.group.name if step.group else None,
        created_at=step.created_at,
        updated_at=step.updated_at,
        problems=problems,
        problem_count=len(step.step_problems),
    )


@router.delete(
    "/{step_id}/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_problem_from_step(
    step_id: int,
    problem_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Remove problem from step: step_id={step_id}, problem_id={problem_id}, user={current_user.username}"
    )
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        logger.warning(f"Step {step_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    if step.created_by != current_user.id:
        logger.warning(
            f"Step {step_id}: user {current_user.username} is not the creator"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the creator of this step",
        )
    step_problem = (
        db.query(StepProblem)
        .filter(StepProblem.step_id == step_id, StepProblem.problem_id == problem_id)
        .first()
    )
    if not step_problem:
        logger.warning(f"Problem {problem_id} not in step {step_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found in this step",
        )
    db.delete(step_problem)
    db.commit()
    logger.success(f"Removed problem {problem_id} from step {step_id}")
