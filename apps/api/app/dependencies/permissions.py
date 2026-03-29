from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.routers.auth import get_current_user
from db.models.group_user import GroupRole, GroupUser
from db.models.user import User
from db.session import get_db


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required",
        )
    return current_user


def require_group_admin(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.is_super_admin:
        return current_user
    gu = (
        db.query(GroupUser)
        .filter(
            GroupUser.group_id == group_id,
            GroupUser.user_id == current_user.id,
            GroupUser.role == GroupRole.ADMIN,
        )
        .first()
    )
    if gu is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group admin privileges required",
        )
    return current_user


def require_group_member(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if current_user.is_super_admin:
        return current_user
    gu = (
        db.query(GroupUser)
        .filter(
            GroupUser.group_id == group_id,
            GroupUser.user_id == current_user.id,
        )
        .first()
    )
    if gu is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group member required",
        )
    return current_user
