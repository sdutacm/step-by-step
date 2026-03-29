from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from db.models import GroupUser, SourceUser, User
from db.models.group_user import GroupRole
from db.session import get_db
from schemas.user import (
    ClaimGhostRequest,
    ClaimGhostResponse,
    GhostAccountListResponse,
    GhostAccountResponse,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from sources import SDUT, VJ

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Auth failed: user '{username}' not found")
        return None
    if not verify_password(
        password,
        str(user.hashed_password) if user.hashed_password is not None else "",
    ):
        logger.warning(f"Auth failed: invalid password for user '{username}'")
        return None
    logger.debug(f"User '{username}' authenticated successfully")
    return user


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Register attempt: username={user_data.username}")
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(
            f"Register failed: username '{user_data.username}' already exists"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user_count = db.query(func.count(User.id)).scalar()
    is_first_user = user_count == 0

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        is_super_admin=is_first_user,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.success(
        f"User '{user_data.username}' registered successfully with id={new_user.id}, is_super_admin={new_user.is_super_admin}"
    )
    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    logger.info(f"Login attempt: username={form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.error(f"Login failed for username '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.success(f"User '{form_data.username}' logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    logger.debug("Decoding access token")
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Token decode failed: invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    if username is None:
        logger.warning("Token decode failed: missing 'sub' claim")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(User)
        .options(joinedload(User.source_users))
        .filter(User.username == username)
        .first()
    )
    if user is None:
        logger.warning(f"Token valid but user '{username}' not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(f"Current user resolved: {username} (id={user.id})")
    return user


oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login", auto_error=False
)


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    logger.debug(f"Get current user: {current_user.username}")
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(f"Update user '{current_user.username}': {update_data}")
    if update_data.nickname is not None:
        current_user.nickname = update_data.nickname
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url

    db.commit()
    db.refresh(current_user)
    logger.success(f"User '{current_user.username}' updated successfully")
    return current_user


@router.post("/claim-ghost", response_model=ClaimGhostResponse)
async def claim_ghost(
    request: ClaimGhostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        f"Claim ghost: user={current_user.username}, source={request.source}, username={request.username}"
    )

    source_map = {"vj": VJ, "sdut": SDUT}
    source_cls = source_map.get(request.source.lower())
    if not source_cls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source: {request.source}",
        )

    try:
        await source_cls.login(request.username, request.password)
    except Exception as e:
        logger.warning(
            f"Claim ghost failed: OJ login failed for {request.username}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OJ account verification failed",
        )

    existing_source_user = (
        db.query(SourceUser)
        .filter(
            SourceUser.source == request.source,
            SourceUser.username == request.username,
        )
        .first()
    )

    if not existing_source_user:
        new_source_user = SourceUser(
            user_id=current_user.id,
            source=request.source,
            username=request.username,
        )
        db.add(new_source_user)
        db.commit()
        logger.success(
            f"New source user bound: user={current_user.username}, source={request.source}, username={request.username}"
        )
        return ClaimGhostResponse(success=True, message="OJ account bound successfully")

    ghost_user = existing_source_user.user

    if ghost_user and not ghost_user.is_temp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This OJ account is already bound to another user",
        )

    if ghost_user and ghost_user.is_temp:
        ghost_user_group_users = (
            db.query(GroupUser).filter(GroupUser.user_id == ghost_user.id).all()
        )

        current_user_group_ids = {
            gu.group_id
            for gu in db.query(GroupUser)
            .filter(GroupUser.user_id == current_user.id)
            .all()
        }

        for ghost_group_user in ghost_user_group_users:
            if ghost_group_user.group_id not in current_user_group_ids:
                new_group_user = GroupUser(
                    group_id=ghost_group_user.group_id,
                    user_id=current_user.id,
                    role=ghost_group_user.role,
                )
                db.add(new_group_user)
            else:
                current_gu = next(
                    gu
                    for gu in db.query(GroupUser)
                    .filter(
                        GroupUser.user_id == current_user.id,
                        GroupUser.group_id == ghost_group_user.group_id,
                    )
                    .all()
                )
                if ghost_group_user.role == GroupRole.ADMIN:
                    current_gu.role = GroupRole.ADMIN

        existing_source_user.user_id = current_user.id

        db.delete(ghost_user)

        db.commit()
        logger.success(
            f"Ghost account claimed: user={current_user.username}, source={request.source}, username={request.username}"
        )
        return ClaimGhostResponse(
            success=True, message="Ghost account claimed successfully"
        )

    return ClaimGhostResponse(success=True, message="OJ account already bound")


@router.get("/ghost-accounts", response_model=GhostAccountListResponse)
async def get_ghost_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.debug(f"Get ghost accounts: user={current_user.username}")

    source_users = (
        db.query(SourceUser)
        .join(User, SourceUser.user_id == User.id)
        .filter(User.is_temp == True)
        .all()
    )

    ghosts = [
        GhostAccountResponse(
            source=su.source,
            username=su.username,
            nickname=su.nickname,
            bound=False,
        )
        for su in source_users
    ]

    return GhostAccountListResponse(ghosts=ghosts)
