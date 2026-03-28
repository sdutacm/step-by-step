from db.models.source_user import SourceUser
from db.models.user import User
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from schemas.source import SourceBindingRequest
from schemas.user import SourceUserResponse
from sources import sources
from sqlalchemy.orm import Session

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
        f"Bind source attempt: user={current_user.username}, source={binding_data.source}, username={binding_data.username}"
    )
    source = get_source(binding_data.source)
    if source is None:
        logger.warning(f"Source '{binding_data.source}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{binding_data.source}' not found",
        )

    existing = (
        db.query(SourceUser)
        .filter(
            SourceUser.source == binding_data.source,
            SourceUser.username == binding_data.username,
        )
        .first()
    )
    if existing:
        logger.warning(
            f"Username '{binding_data.username}' on '{binding_data.source}' is already bound"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{binding_data.username}' is already bound on this source",
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
        username=binding_data.username,
    )
    db.add(source_user)
    db.commit()
    db.refresh(source_user)
    logger.success(
        f"Source '{binding_data.source}' (username={binding_data.username}) bound to user '{current_user.username}' (id={source_user.id})"
    )
    return source_user


@router.delete("/unbind/{binding_id}")
def unbind_source(
    binding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Unbind binding: user={current_user.username}, binding_id={binding_id}"
    )
    source_user = (
        db.query(SourceUser)
        .filter(
            SourceUser.id == binding_id,
            SourceUser.user_id == current_user.id,
        )
        .first()
    )
    if not source_user:
        logger.warning(
            f"Binding {binding_id} not found for user '{current_user.username}'"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Binding not found",
        )

    db.delete(source_user)
    db.commit()
    logger.success(
        f"Binding {binding_id} ({source_user.source}/{source_user.username}) unbound from user '{current_user.username}'"
    )
    return {"message": "Unbound successfully"}


@router.get("/bindings", response_model=list[SourceUserResponse])
def list_bindings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_users = (
        db.query(SourceUser).filter(SourceUser.user_id == current_user.id).all()
    )
    logger.debug(
        f"List bindings for user '{current_user.username}': {[(su.source, su.username) for su in source_users]}"
    )
    return source_users
