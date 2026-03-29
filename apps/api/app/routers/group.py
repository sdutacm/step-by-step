from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.dependencies.permissions import require_super_admin
from app.routers.auth import get_current_user
from db.models.group import Group
from db.models.group_user import GroupRole, GroupUser
from db.models.user import User
from db.session import get_db
from schemas.group import (
    GroupCreate,
    GroupListItem,
    GroupListResponse,
    GroupResponse,
    GroupUpdate,
)
from schemas.group_user import (
    GroupMemberAddRequest,
    GroupMemberListResponse,
    GroupMemberResponse,
    GroupMemberUpdateRequest,
)

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Create group: user={current_user.username}, name={group_data.name}")
    existing = db.query(Group).filter(Group.name == group_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already exists",
        )
    group = Group(name=group_data.name, description=group_data.description)
    db.add(group)
    db.commit()
    db.refresh(group)

    group_user = GroupUser(
        group_id=group.id,
        user_id=current_user.id,
        role=GroupRole.ADMIN,
    )
    db.add(group_user)
    db.commit()
    db.refresh(group)

    logger.success(f"Group created: id={group.id}, name={group.name}")
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=1,
        step_count=0,
    )


@router.get("", response_model=GroupListResponse)
def list_groups(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    logger.debug(f"List groups: page={page}, page_size={page_size}")
    total = db.query(func.count(Group.id)).scalar()
    groups = (
        db.query(Group)
        .options(joinedload(Group.group_users), joinedload(Group.steps))
        .order_by(Group.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        GroupListItem(
            id=g.id,
            name=g.name,
            description=g.description,
            created_at=g.created_at,
            updated_at=g.updated_at,
            member_count=len(g.group_users),
            step_count=len(g.steps),
        )
        for g in groups
    ]
    return GroupListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
):
    logger.debug(f"Get group: id={group_id}")
    group = (
        db.query(Group)
        .options(joinedload(Group.group_users), joinedload(Group.steps))
        .filter(Group.id == group_id)
        .first()
    )
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=len(group.group_users),
        step_count=len(group.steps),
    )


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    update_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Update group: id={group_id}, user={current_user.username}")
    if current_user.is_super_admin:
        pass
    else:
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
                detail="Only group admin can update group",
            )
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    if update_data.name is not None:
        existing = db.query(Group).filter(Group.name == update_data.name).first()
        if existing and existing.id != group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group name already exists",
            )
        group.name = update_data.name
    if update_data.description is not None:
        group.description = update_data.description
    db.commit()
    db.refresh(group)
    logger.success(f"Group {group_id} updated")
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=len(group.group_users),
        step_count=len(group.steps),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    logger.info(f"Delete group: id={group_id}, user={current_user.username}")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    db.delete(group)
    db.commit()
    logger.success(f"Group {group_id} deleted")


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    group_id: int,
    request: GroupMemberAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Add member: group_id={group_id}, admin={current_user.username}, target={request.username}"
    )
    if not current_user.is_super_admin:
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
                detail="Only group admin can add members",
            )
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    target_user = db.query(User).filter(User.username == request.username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    existing = (
        db.query(GroupUser)
        .filter(GroupUser.group_id == group_id, GroupUser.user_id == target_user.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group",
        )
    group_user = GroupUser(
        group_id=group_id,
        user_id=target_user.id,
        role=GroupRole.MEMBER,
    )
    db.add(group_user)
    db.commit()
    db.refresh(group_user)
    logger.success(f"Member added: user_id={target_user.id} to group_id={group_id}")
    return GroupMemberResponse(
        id=group_user.id,
        user_id=target_user.id,
        username=target_user.username,
        nickname=target_user.nickname,
        role=group_user.role,
        joined_at=group_user.joined_at,
    )


@router.get("/{group_id}/members", response_model=GroupMemberListResponse)
def list_members(
    group_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    logger.debug(
        f"List members: group_id={group_id}, page={page}, page_size={page_size}"
    )
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
    items = [
        GroupMemberResponse(
            id=gu.id,
            user_id=gu.user.id,
            username=gu.user.username,
            nickname=gu.user.nickname,
            role=gu.role,
            joined_at=gu.joined_at,
        )
        for gu in members
    ]
    return GroupMemberListResponse(
        total=total, page=page, page_size=page_size, items=items
    )


@router.patch("/{group_id}/members/{user_id}", response_model=GroupMemberResponse)
def update_member(
    group_id: int,
    user_id: int,
    update_data: GroupMemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Update member: group_id={group_id}, user_id={user_id}, admin={current_user.username}"
    )
    if not current_user.is_super_admin:
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
                detail="Only group admin can update members",
            )
    group_user = (
        db.query(GroupUser)
        .options(joinedload(GroupUser.user))
        .filter(GroupUser.group_id == group_id, GroupUser.user_id == user_id)
        .first()
    )
    if not group_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group",
        )
    group_user.role = update_data.role
    db.commit()
    db.refresh(group_user)
    logger.success(f"Member role updated: user_id={user_id} in group_id={group_id}")
    return GroupMemberResponse(
        id=group_user.id,
        user_id=group_user.user.id,
        username=group_user.user.username,
        nickname=group_user.user.nickname,
        role=group_user.role,
        joined_at=group_user.joined_at,
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Remove member: group_id={group_id}, user_id={user_id}, admin={current_user.username}"
    )
    if not current_user.is_super_admin:
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
                detail="Only group admin can remove members",
            )
    group_user = (
        db.query(GroupUser)
        .filter(GroupUser.group_id == group_id, GroupUser.user_id == user_id)
        .first()
    )
    if not group_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group",
        )
    db.delete(group_user)
    db.commit()
    logger.success(f"Member removed: user_id={user_id} from group_id={group_id}")
