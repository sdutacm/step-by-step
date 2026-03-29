from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.dependencies.permissions import require_group_admin
from app.routers.auth import get_current_user, get_current_user_optional
from db.models.board import (
    Board,
    BoardStepUser,
)
from db.models.board import (
    BoardVisibility as BoardVisibilityModel,
)
from db.models.group import Group
from db.models.group_user import GroupUser
from db.models.problem import Problem
from db.models.solution import Solution
from db.models.source_user import SourceUser
from db.models.step import Step
from db.models.step_problem import StepProblem
from db.models.user import User
from db.session import get_db
from schemas.board import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    BoardCreate,
    BoardListItem,
    BoardListResponse,
    BoardProgressResponse,
    BoardResponse,
    BoardUpdate,
    BoardVisibility,
    ProblemProgress,
    StepProgress,
    UserBoardProgress,
)
from schemas.result import ResultEnum

router = APIRouter(prefix="/api", tags=["boards"])


def check_board_visibility(
    board: Board,
    current_user: User | None,
    db: Session,
) -> bool:
    if board.visibility == BoardVisibilityModel.PUBLIC:
        return True
    if current_user is None:
        return False
    if board.visibility == BoardVisibilityModel.BOARD_USER:
        bsu = (
            db.query(BoardStepUser)
            .filter(
                BoardStepUser.board_id == board.id,
                BoardStepUser.user_id == current_user.id,
            )
            .first()
        )
        return bsu is not None
    if board.visibility == BoardVisibilityModel.GROUP_MEMBER:
        gu = (
            db.query(GroupUser)
            .filter(
                GroupUser.group_id == board.group_id,
                GroupUser.user_id == current_user.id,
            )
            .first()
        )
        return gu is not None
    return False


def get_user_source_usernames(db: Session, user_id: int) -> dict[str, str]:
    source_users = db.query(SourceUser).filter(SourceUser.user_id == user_id).all()
    return {su.source: su.username for su in source_users}


def calculate_user_step_progress(
    db: Session,
    user_id: int,
    step_id: int,
    source_usernames: dict[str, str],
) -> StepProgress:
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {step_id} not found",
        )

    step_problems = (
        db.query(StepProblem)
        .filter(StepProblem.step_id == step_id)
        .order_by(StepProblem.order)
        .all()
    )

    solved_map: dict[int, datetime] = {}
    for sp in step_problems:
        solutions = (
            db.query(Solution)
            .filter(
                Solution.problem_id == sp.problem_id,
                Solution.result == ResultEnum.Accepted,
            )
            .all()
        )
        for sol in solutions:
            src_username = source_usernames.get(sol.source)
            if src_username and sol.username == src_username:
                if sp.problem_id not in solved_map:
                    solved_map[sp.problem_id] = sol.submitted_at
                elif sol.submitted_at < solved_map[sp.problem_id]:
                    solved_map[sp.problem_id] = sol.submitted_at

    problems: list[ProblemProgress] = []
    for sp in step_problems:
        problem = sp.problem
        ac_time = solved_map.get(sp.problem_id)
        problems.append(
            ProblemProgress(
                problem_id=sp.problem_id,
                oj_problem_id=problem.problem_id,
                title=problem.title,
                order=sp.order,
                specialty=sp.specialty,
                topic=sp.topic,
                ac_time=ac_time,
            )
        )

    solved_count = len(solved_map)
    total_count = len(step_problems)
    progress_percent = (solved_count / total_count * 100) if total_count > 0 else 0

    if solved_count == 0:
        status_str = "not_started"
    elif solved_count == total_count:
        status_str = "completed"
    else:
        status_str = "in_progress"

    return StepProgress(
        step_id=step_id,
        step_title=step.title,
        total_problems=total_count,
        solved_problems=solved_count,
        progress_percent=progress_percent,
        status=status_str,
        problems=problems,
    )


@router.post(
    "/groups/{group_id}/boards",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_board(
    group_id: int,
    board_data: BoardCreate,
    current_user: User = Depends(require_group_admin),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Create board: group_id={group_id}, name={board_data.name}, user={current_user.username}"
    )
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    board = Board(
        name=board_data.name,
        description=board_data.description,
        visibility=board_data.visibility,
        group_id=group_id,
        created_by=current_user.id,
    )
    db.add(board)
    db.commit()
    db.refresh(board)

    logger.success(f"Board created: id={board.id}, name={board.name}")
    return BoardResponse(
        id=board.id,
        name=board.name,
        description=board.description,
        visibility=board.visibility,
        group_id=board.group_id,
        group_name=group.name,
        created_by=board.created_by,
        creator_username=current_user.username,
        created_at=board.created_at,
        updated_at=board.updated_at,
        member_count=0,
    )


@router.get("/groups/{group_id}/boards", response_model=BoardListResponse)
def list_boards(
    group_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    logger.debug(
        f"List boards: group_id={group_id}, page={page}, page_size={page_size}"
    )
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    total = db.query(func.count(Board.id)).filter(Board.group_id == group_id).scalar()

    boards = (
        db.query(Board)
        .options(joinedload(Board.creator))
        .filter(Board.group_id == group_id)
        .order_by(Board.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for board in boards:
        if not check_board_visibility(board, current_user, db):
            continue
        items.append(
            BoardListItem(
                id=board.id,
                name=board.name,
                description=board.description,
                visibility=board.visibility,
                group_id=board.group_id,
                created_by=board.created_by,
                creator_username=board.creator.username if board.creator else "",
                created_at=board.created_at,
                updated_at=board.updated_at,
            )
        )

    visible_items = [item for item in items]

    return BoardListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=visible_items,
    )


@router.get("/boards/{board_id}", response_model=BoardResponse)
def get_board(
    board_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    logger.debug(f"Get board: id={board_id}")
    board = (
        db.query(Board)
        .options(joinedload(Board.creator), joinedload(Board.group))
        .filter(Board.id == board_id)
        .first()
    )
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not check_board_visibility(board, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this board",
        )

    assignment_count = (
        db.query(func.count(BoardStepUser.id))
        .filter(BoardStepUser.board_id == board_id)
        .scalar()
    )

    return BoardResponse(
        id=board.id,
        name=board.name,
        description=board.description,
        visibility=board.visibility,
        group_id=board.group_id,
        group_name=board.group.name if board.group else None,
        created_by=board.created_by,
        creator_username=board.creator.username if board.creator else "",
        created_at=board.created_at,
        updated_at=board.updated_at,
        member_count=assignment_count,
    )


@router.patch("/boards/{board_id}", response_model=BoardResponse)
def update_board(
    board_id: int,
    update_data: BoardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Update board: id={board_id}, user={current_user.username}")
    board = (
        db.query(Board)
        .options(joinedload(Board.creator), joinedload(Board.group))
        .filter(Board.id == board_id)
        .first()
    )
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not current_user.is_super_admin:
        gu = (
            db.query(GroupUser)
            .filter(
                GroupUser.group_id == board.group_id,
                GroupUser.user_id == current_user.id,
                GroupUser.role == "admin",
            )
            .first()
        )
        if gu is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admin can update board",
            )

    if update_data.name is not None:
        board.name = update_data.name
    if update_data.description is not None:
        board.description = update_data.description
    if update_data.visibility is not None:
        board.visibility = update_data.visibility

    db.commit()
    db.refresh(board)

    assignment_count = (
        db.query(func.count(BoardStepUser.id))
        .filter(BoardStepUser.board_id == board_id)
        .scalar()
    )

    logger.success(f"Board {board_id} updated")
    return BoardResponse(
        id=board.id,
        name=board.name,
        description=board.description,
        visibility=board.visibility,
        group_id=board.group_id,
        group_name=board.group.name if board.group else None,
        created_by=board.created_by,
        creator_username=board.creator.username if board.creator else "",
        created_at=board.created_at,
        updated_at=board.updated_at,
        member_count=assignment_count,
    )


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(
    board_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Delete board: id={board_id}, user={current_user.username}")
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not current_user.is_super_admin:
        gu = (
            db.query(GroupUser)
            .filter(
                GroupUser.group_id == board.group_id,
                GroupUser.user_id == current_user.id,
                GroupUser.role == "admin",
            )
            .first()
        )
        if gu is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admin can delete board",
            )

    db.delete(board)
    db.commit()
    logger.success(f"Board {board_id} deleted")


@router.get(
    "/boards/{board_id}/assignments",
    response_model=AssignmentListResponse,
)
def get_assignments(
    board_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    logger.debug(f"Get assignments: board_id={board_id}")
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not check_board_visibility(board, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this board",
        )

    assignments = (
        db.query(BoardStepUser)
        .options(joinedload(BoardStepUser.step), joinedload(BoardStepUser.user))
        .filter(BoardStepUser.board_id == board_id)
        .all()
    )

    items = [
        AssignmentResponse(
            id=a.id,
            board_id=a.board_id,
            step_id=a.step_id,
            user_id=a.user_id,
            step_title=a.step.title if a.step else "",
            username=a.user.username if a.user else "",
            created_at=a.created_at,
        )
        for a in assignments
    ]

    return AssignmentListResponse(total=len(items), items=items)


@router.post(
    "/boards/{board_id}/assignments",
    response_model=AssignmentListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignments(
    board_id: int,
    assignments: list[AssignmentCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Create assignments: board_id={board_id}, count={len(assignments)}, user={current_user.username}"
    )
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not current_user.is_super_admin:
        gu = (
            db.query(GroupUser)
            .filter(
                GroupUser.group_id == board.group_id,
                GroupUser.user_id == current_user.id,
                GroupUser.role == "admin",
            )
            .first()
        )
        if gu is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admin can manage assignments",
            )

    created: list[BoardStepUser] = []
    for assignment in assignments:
        step = db.query(Step).filter(Step.id == assignment.step_id).first()
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Step {assignment.step_id} not found",
            )
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {assignment.user_id} not found",
            )

        existing = (
            db.query(BoardStepUser)
            .filter(
                BoardStepUser.board_id == board_id,
                BoardStepUser.step_id == assignment.step_id,
                BoardStepUser.user_id == assignment.user_id,
            )
            .first()
        )
        if existing:
            continue

        bsu = BoardStepUser(
            board_id=board_id,
            step_id=assignment.step_id,
            user_id=assignment.user_id,
        )
        db.add(bsu)
        created.append(bsu)

    db.commit()

    for bsu in created:
        db.refresh(bsu)

    items = []
    for bsu in created:
        step = db.query(Step).filter(Step.id == bsu.step_id).first()
        user = db.query(User).filter(User.id == bsu.user_id).first()
        items.append(
            AssignmentResponse(
                id=bsu.id,
                board_id=bsu.board_id,
                step_id=bsu.step_id,
                user_id=bsu.user_id,
                step_title=step.title if step else "",
                username=user.username if user else "",
                created_at=bsu.created_at,
            )
        )

    logger.success(f"Assignments created: board_id={board_id}, count={len(created)}")
    return AssignmentListResponse(total=len(items), items=items)


@router.delete(
    "/boards/{board_id}/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assignment(
    board_id: int,
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Delete assignment: board_id={board_id}, assignment_id={assignment_id}, user={current_user.username}"
    )
    board = db.query(Board).filter(Board.id == board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not current_user.is_super_admin:
        gu = (
            db.query(GroupUser)
            .filter(
                GroupUser.group_id == board.group_id,
                GroupUser.user_id == current_user.id,
                GroupUser.role == "admin",
            )
            .first()
        )
        if gu is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group admin can manage assignments",
            )

    assignment = (
        db.query(BoardStepUser)
        .filter(
            BoardStepUser.id == assignment_id,
            BoardStepUser.board_id == board_id,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    db.delete(assignment)
    db.commit()
    logger.success(f"Assignment {assignment_id} deleted")


@router.get("/boards/{board_id}/progress", response_model=BoardProgressResponse)
def get_board_progress(
    board_id: int,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.debug(f"Get board progress: board_id={board_id}")
    board = (
        db.query(Board)
        .options(joinedload(Board.group))
        .filter(Board.id == board_id)
        .first()
    )
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    if not check_board_visibility(board, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this board",
        )

    assignments = (
        db.query(BoardStepUser)
        .options(joinedload(BoardStepUser.user), joinedload(BoardStepUser.step))
        .filter(BoardStepUser.board_id == board_id)
        .all()
    )

    user_step_map: dict[int, list[int]] = {}
    for a in assignments:
        if a.user_id not in user_step_map:
            user_step_map[a.user_id] = []
        user_step_map[a.user_id].append(a.step_id)

    result_users: list[UserBoardProgress] = []
    for user_id, step_ids in user_step_map.items():
        user_obj = next((a.user for a in assignments if a.user_id == user_id), None)
        if not user_obj:
            continue

        source_usernames = get_user_source_usernames(db, user_id)

        steps_progress: list[StepProgress] = []
        total_solved = 0
        total_problems = 0

        for step_id in step_ids:
            step_progress = calculate_user_step_progress(
                db, user_id, step_id, source_usernames
            )
            steps_progress.append(step_progress)
            total_solved += step_progress.solved_problems
            total_problems += step_progress.total_problems

        result_users.append(
            UserBoardProgress(
                user_id=user_id,
                username=user_obj.username,
                nickname=user_obj.nickname,
                steps=steps_progress,
                total_solved=total_solved,
                total_problems=total_problems,
            )
        )

    return BoardProgressResponse(
        board_id=board_id,
        board_name=board.name,
        group_id=board.group_id,
        users=result_users,
    )
