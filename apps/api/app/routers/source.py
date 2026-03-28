from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from db.session import get_db
from db.models.user import User
from db.models.source_user import SourceUser
from schemas.source import SourceBindingRequest
from schemas.user import SourceUserResponse
from sources import sources
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/sources", tags=["sources"])


def get_source(source_name: str):
    for source in sources:
        if source.source == source_name:
            return source
    return None


@router.get("")
def list_sources():
    logger.debug(f"List sources: {[s.source for s in sources]}")
    return [{"source": s.source} for s in sources]


@router.post("/bind", response_model=SourceUserResponse)
async def bind_source(
    binding_data: SourceBindingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Bind source attempt: user={current_user.username}, source={binding_data.source}"
    )
    source = get_source(binding_data.source)
    if source is None:
        logger.warning(f"Source '{binding_data.source}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{binding_data.source}' not found",
        )

    existing = (
        db.query(SourceUser).filter(SourceUser.source == binding_data.source).first()
    )
    if existing:
        logger.warning(f"Source '{binding_data.source}' already bound to another user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source '{binding_data.source}' is already bound to another user",
        )

    user_existing = (
        db.query(SourceUser)
        .filter(
            SourceUser.source == binding_data.source,
            SourceUser.user_id == current_user.id,
        )
        .first()
    )
    if user_existing:
        logger.warning(
            f"Source '{binding_data.source}' already bound to user '{current_user.username}'"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source '{binding_data.source}' is already bound to your account",
        )

    logger.debug(
        f"Attempting to login to {binding_data.source} with username={binding_data.username}"
    )
    login_result = await source.login(binding_data.username, binding_data.password)
    if not login_result:
        logger.error(
            f"Login failed for source '{binding_data.source}' with username={binding_data.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password for this source",
        )

    source_user = SourceUser(
        user_id=current_user.id,
        source=binding_data.source,
    )
    db.add(source_user)
    db.commit()
    db.refresh(source_user)
    logger.success(
        f"Source '{binding_data.source}' bound to user '{current_user.username}' (id={source_user.id})"
    )
    return source_user


@router.delete("/unbind/{source}")
def unbind_source(
    source: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Unbind source: user={current_user.username}, source={source}")
    source_user = (
        db.query(SourceUser)
        .filter(
            SourceUser.source == source,
            SourceUser.user_id == current_user.id,
        )
        .first()
    )
    if not source_user:
        logger.warning(
            f"Source '{source}' is not bound to user '{current_user.username}'"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source}' is not bound to your account",
        )

    db.delete(source_user)
    db.commit()
    logger.success(f"Source '{source}' unbound from user '{current_user.username}'")
    return {"message": f"Source '{source}' unbound successfully"}


@router.get("/bindings", response_model=list[SourceUserResponse])
def list_bindings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_users = (
        db.query(SourceUser).filter(SourceUser.user_id == current_user.id).all()
    )
    logger.debug(
        f"List bindings for user '{current_user.username}': {[su.source for su in source_users]}"
    )
    return source_users
