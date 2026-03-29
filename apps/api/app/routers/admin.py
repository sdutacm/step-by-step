from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.dependencies.permissions import require_super_admin
from db.models.group import Group
from db.models.group_user import GroupUser
from db.models.user import User
from db.session import get_db
from schemas.admin import (
    UserListItem,
    UserListResponse,
    UserResponse,
    UserSuperAdminUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    logger.debug(f"List users: page={page}, page_size={page_size}")
    total = db.query(func.count(User.id)).scalar()
    users = (
        db.query(User)
        .order_by(User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        UserListItem(
            id=u.id,
            username=u.username,
            nickname=u.nickname,
            avatar_url=u.avatar_url,
            is_super_admin=u.is_super_admin,
        )
        for u in users
    ]
    return UserListResponse(total=total, page=page, page_size=page_size, items=items)


@router.patch("/users/{user_id}/super-admin", response_model=UserResponse)
def update_user_super_admin(
    user_id: int,
    update_data: UserSuperAdminUpdate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Update user {user_id} super_admin to {update_data.is_super_admin}")
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own super admin status",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.is_super_admin = update_data.is_super_admin
    db.commit()
    db.refresh(user)
    logger.success(
        f"User {user_id} super_admin updated to {update_data.is_super_admin}"
    )
    return UserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        is_super_admin=user.is_super_admin,
    )


@router.get("/groups/{group_id}/members")
def list_group_members_admin(
    group_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    logger.debug(f"Admin list group members: group_id={group_id}")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    total = (
        db.query(func.count(GroupUser.id))
        .filter(GroupUser.group_id == group_id)
        .scalar()
    )
    members = (
        db.query(GroupUser)
        .options(joinedload(GroupUser.user))
        .filter(GroupUser.group_id == group_id)
        .order_by(GroupUser.joined_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": gu.id,
                "user_id": gu.user.id,
                "username": gu.user.username,
                "nickname": gu.user.nickname,
                "role": gu.role.value,
                "joined_at": gu.joined_at.isoformat(),
            }
            for gu in members
        ],
    }
