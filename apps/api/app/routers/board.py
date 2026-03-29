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
    BoardUser,
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
    BoardCreate,
    BoardListItem,
    BoardListResponse,
    BoardProgressResponse,
    BoardResponse,
    BoardUpdate,
    BoardUserListResponse,
    BoardUserResponse,
    ProblemProgress,
    PublicBoardListItem,
    PublicBoardListResponse,
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
        bu = (
            db.query(BoardUser)
            .filter(
                BoardUser.board_id == board.id,
                BoardUser.user_id == current_user.id,
            )
            .first()
        )
        return bu is not None
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
) -> tuple[int, int, list[ProblemProgress]]:
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        return 0, 0, []

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
                source=problem.source,
                title=problem.title,
                order=sp.order,
                specialty=sp.specialty,
                topic=sp.topic,
                ac_time=ac_time,
            )
        )

    solved_count = len(solved_map)
    total_count = len(step_problems)

    return solved_count, total_count, problems


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

    step = db.query(Step).filter(Step.id == board_data.step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    board = Board(
        name=board_data.name,
        description=board_data.description,
        visibility=board_data.visibility,
        group_id=group_id,
        created_by=current_user.id,
        step_id=board_data.step_id,
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
        step_id=board.step_id,
        step_title=step.title,
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
        .options(joinedload(Board.creator), joinedload(Board.step))
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


@router.get("/boards/public", response_model=PublicBoardListResponse)
def list_public_boards(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    logger.debug(f"List public boards: page={page}, page_size={page_size}")

    total = (
        db.query(func.count(Board.id))
        .filter(Board.visibility == BoardVisibilityModel.PUBLIC)
        .scalar()
    )

    boards = (
        db.query(Board)
        .options(
            joinedload(Board.creator), joinedload(Board.group), joinedload(Board.step)
        )
        .filter(Board.visibility == BoardVisibilityModel.PUBLIC)
        .order_by(Board.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        PublicBoardListItem(
            id=board.id,
            name=board.name,
            description=board.description,
            visibility=board.visibility,
            group_id=board.group_id,
            group_name=board.group.name if board.group else None,
            step_id=board.step_id,
            step_title=board.step.title if board.step else "",
            created_by=board.created_by,
            creator_username=board.creator.username if board.creator else "",
            created_at=board.created_at,
            updated_at=board.updated_at,
        )
        for board in boards
    ]

    return PublicBoardListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
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
        .options(
            joinedload(Board.creator), joinedload(Board.group), joinedload(Board.step)
        )
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

    member_count = (
        db.query(func.count(BoardUser.id))
        .filter(BoardUser.board_id == board_id)
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
        step_id=board.step_id,
        step_title=board.step.title if board.step else "",
        member_count=member_count,
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
        .options(
            joinedload(Board.creator), joinedload(Board.group), joinedload(Board.step)
        )
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
    if update_data.step_id is not None:
        step = db.query(Step).filter(Step.id == update_data.step_id).first()
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Step not found",
            )
        board.step_id = update_data.step_id

    db.commit()
    db.refresh(board)

    member_count = (
        db.query(func.count(BoardUser.id))
        .filter(BoardUser.board_id == board_id)
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
        step_id=board.step_id,
        step_title=board.step.title if board.step else "",
        member_count=member_count,
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
    "/boards/{board_id}/users",
    response_model=BoardUserListResponse,
)
def get_board_users(
    board_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    logger.debug(f"Get board users: board_id={board_id}")
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

    board_users = (
        db.query(BoardUser)
        .options(joinedload(BoardUser.user))
        .filter(BoardUser.board_id == board_id)
        .all()
    )

    items = [
        BoardUserResponse(
            id=bu.id,
            board_id=bu.board_id,
            user_id=bu.user_id,
            username=bu.user.username if bu.user else "",
            nickname=bu.user.nickname if bu.user else None,
            created_at=bu.created_at,
        )
        for bu in board_users
    ]

    return BoardUserListResponse(total=len(items), items=items)


@router.post(
    "/boards/{board_id}/users",
    response_model=BoardUserListResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_board_users(
    board_id: int,
    user_ids: list[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Create board users: board_id={board_id}, user_ids={user_ids}, user={current_user.username}"
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
                detail="Only group admin can manage board users",
            )

    created: list[BoardUser] = []
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found",
            )

        existing = (
            db.query(BoardUser)
            .filter(
                BoardUser.board_id == board_id,
                BoardUser.user_id == user_id,
            )
            .first()
        )
        if existing:
            continue

        bu = BoardUser(
            board_id=board_id,
            user_id=user_id,
        )
        db.add(bu)
        created.append(bu)

    db.commit()

    for bu in created:
        db.refresh(bu)

    items = []
    for bu in created:
        user = db.query(User).filter(User.id == bu.user_id).first()
        items.append(
            BoardUserResponse(
                id=bu.id,
                board_id=bu.board_id,
                user_id=bu.user_id,
                username=user.username if user else "",
                nickname=user.nickname if user else None,
                created_at=bu.created_at,
            )
        )

    logger.success(f"Board users created: board_id={board_id}, count={len(created)}")
    return BoardUserListResponse(total=len(items), items=items)


@router.delete(
    "/boards/{board_id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_board_user(
    board_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Delete board user: board_id={board_id}, user_id={user_id}, user={current_user.username}"
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
                detail="Only group admin can manage board users",
            )

    board_user = (
        db.query(BoardUser)
        .filter(
            BoardUser.board_id == board_id,
            BoardUser.user_id == user_id,
        )
        .first()
    )
    if not board_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board user not found",
        )

    db.delete(board_user)
    db.commit()
    logger.success(f"Board user {user_id} deleted from board {board_id}")


@router.get("/boards/{board_id}/progress", response_model=BoardProgressResponse)
def get_board_progress(
    board_id: int,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.debug(f"Get board progress: board_id={board_id}")
    board = (
        db.query(Board)
        .options(joinedload(Board.group), joinedload(Board.step))
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

    board_users = (
        db.query(BoardUser)
        .options(joinedload(BoardUser.user))
        .filter(BoardUser.board_id == board_id)
        .all()
    )

    step = db.query(Step).filter(Step.id == board.step_id).first()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    result_users: list[UserBoardProgress] = []
    for bu in board_users:
        source_usernames = get_user_source_usernames(db, bu.user_id)
        solved_count, total_count, problems = calculate_user_step_progress(
            db, bu.user_id, board.step_id, source_usernames
        )

        progress_percent = (solved_count / total_count * 100) if total_count > 0 else 0
        if solved_count == 0:
            status_str = "not_started"
        elif solved_count == total_count:
            status_str = "completed"
        else:
            status_str = "in_progress"

        result_users.append(
            UserBoardProgress(
                user_id=bu.user_id,
                username=bu.user.username if bu.user else "",
                nickname=bu.user.nickname if bu.user else None,
                solved_problems=solved_count,
                total_problems=total_count,
                progress_percent=progress_percent,
                status=status_str,
                problems=problems,
            )
        )

    return BoardProgressResponse(
        board_id=board_id,
        board_name=board.name,
        step_id=board.step_id,
        step_title=step.title,
        group_id=board.group_id,
        users=result_users,
    )
