from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.routers.auth import get_current_user
from db.models.group import Group
from db.models.group_step_progress import GroupStepProgress
from db.models.group_user import GroupRole, GroupUser
from db.models.step import Step
from db.models.step_problem import StepProblem
from db.models.user import User
from db.session import get_db
from schemas.group_progress import (
    GroupProblemProgress,
    GroupProgressResponse,
    GroupUserProgress,
)
from schemas.group_progress import (
    GroupStepProgress as GroupStepProgressSchema,
)

router = APIRouter(prefix="/api/groups/{group_id}/progress", tags=["group-progress"])


def is_group_member(db: Session, user_id: int, group_id: int) -> bool:
    gu = (
        db.query(GroupUser)
        .filter(GroupUser.user_id == user_id, GroupUser.group_id == group_id)
        .first()
    )
    return gu is not None


@router.get("", response_model=GroupProgressResponse)
def get_group_progress(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.debug(
        f"Get group progress: group_id={group_id}, user={current_user.username}"
    )
    if not is_group_member(db, current_user.id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can view progress",
        )
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    members = (
        db.query(GroupUser)
        .options(joinedload(GroupUser.user))
        .filter(GroupUser.group_id == group_id)
        .all()
    )

    steps = db.query(Step).filter(Step.group_id == group_id).all()

    progress_records = (
        db.query(GroupStepProgress).filter(GroupStepProgress.group_id == group_id).all()
    )

    user_progress_map: dict[int, dict[int, list[GroupStepProgress]]] = {}
    for rec in progress_records:
        if rec.user_id not in user_progress_map:
            user_progress_map[rec.user_id] = {}
        if rec.step_id not in user_progress_map[rec.user_id]:
            user_progress_map[rec.user_id][rec.step_id] = []
        user_progress_map[rec.user_id][rec.step_id].append(rec)

    result_members: list[GroupUserProgress] = []
    for member in members:
        user_id = member.user_id
        user_steps: list[GroupStepProgressSchema] = []
        total_solved = 0

        for step in steps:
            step_problems = (
                db.query(StepProblem).filter(StepProblem.step_id == step.id).all()
            )
            total_problems = len(step_problems)

            user_records = user_progress_map.get(user_id, {}).get(step.id, [])
            solved_problems: list[GroupProblemProgress] = []
            for rec in user_records:
                step_problem = next(
                    (sp for sp in step_problems if sp.problem_id == rec.problem_id),
                    None,
                )
                if step_problem:
                    solved_problems.append(
                        GroupProblemProgress(
                            problem_id=rec.problem_id,
                            oj_problem_id=step_problem.problem.problem_id,
                            title=step_problem.problem.title,
                            ac_time=rec.ac_time,
                            order=step_problem.order,
                        )
                    )
                    total_solved += 1

            progress_percent = (
                (len(solved_problems) / total_problems * 100)
                if total_problems > 0
                else 0
            )
            user_steps.append(
                GroupStepProgressSchema(
                    step_id=step.id,
                    step_title=step.title,
                    total_problems=total_problems,
                    solved_problems=len(solved_problems),
                    progress_percent=progress_percent,
                    problems=solved_problems,
                )
            )

        result_members.append(
            GroupUserProgress(
                user_id=user_id,
                username=member.user.username,
                nickname=member.user.nickname,
                steps=user_steps,
                total_solved=total_solved,
            )
        )

    return GroupProgressResponse(
        group_id=group_id,
        group_name=group.name,
        members=result_members,
    )


@router.get("/{user_id}", response_model=GroupUserProgress)
def get_user_progress(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.debug(
        f"Get user progress: group_id={group_id}, target_user_id={user_id}, user={current_user.username}"
    )
    if not is_group_member(db, current_user.id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group members can view progress",
        )
    target_member = (
        db.query(GroupUser)
        .options(joinedload(GroupUser.user))
        .filter(GroupUser.group_id == group_id, GroupUser.user_id == user_id)
        .first()
    )
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group",
        )

    steps = db.query(Step).filter(Step.group_id == group_id).all()
    progress_records = (
        db.query(GroupStepProgress)
        .filter(
            GroupStepProgress.group_id == group_id, GroupStepProgress.user_id == user_id
        )
        .all()
    )

    step_progress_map: dict[int, list[GroupStepProgress]] = {}
    for rec in progress_records:
        if rec.step_id not in step_progress_map:
            step_progress_map[rec.step_id] = []
        step_progress_map[rec.step_id].append(rec)

    user_steps: list[GroupStepProgressSchema] = []
    total_solved = 0

    for step in steps:
        step_problems = (
            db.query(StepProblem).filter(StepProblem.step_id == step.id).all()
        )
        total_problems = len(step_problems)

        user_records = step_progress_map.get(step.id, [])
        solved_problems: list[GroupProblemProgress] = []
        for rec in user_records:
            step_problem = next(
                (sp for sp in step_problems if sp.problem_id == rec.problem_id),
                None,
            )
            if step_problem:
                solved_problems.append(
                    GroupProblemProgress(
                        problem_id=rec.problem_id,
                        oj_problem_id=step_problem.problem.problem_id,
                        title=step_problem.problem.title,
                        ac_time=rec.ac_time,
                        order=step_problem.order,
                    )
                )
                total_solved += 1

        progress_percent = (
            (len(solved_problems) / total_problems * 100) if total_problems > 0 else 0
        )
        user_steps.append(
            GroupStepProgressSchema(
                step_id=step.id,
                step_title=step.title,
                total_problems=total_problems,
                solved_problems=len(solved_problems),
                progress_percent=progress_percent,
                problems=solved_problems,
            )
        )

    return GroupUserProgress(
        user_id=user_id,
        username=target_member.user.username,
        nickname=target_member.user.nickname,
        steps=user_steps,
        total_solved=total_solved,
    )
