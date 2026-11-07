
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Employee
from app.schemas import (
    LoginRequest,
    UserCreate,
    UserResponse,
    TokenResponse,
)
from app.security.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.security.dependencies import get_current_user, require_roles
from app.security.utils import (
    create_access_token,
    verify_password,
    hash_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == str(payload.email).lower())
        .first()
    )

    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=str(user.id),
        role=user.role,
    )

    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin")),
):
    email = str(payload.email).lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    if payload.employee_id is not None:
        employee_exists = (
    db.query(Employee)
    .filter(Employee.id == payload.employee_id)
    .first()
)

        if employee_exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The specified employee does not exist.",
            )

        linked_user = (
            db.query(User)
            .filter(User.employee_id == payload.employee_id)
            .first()
        )

        if linked_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This employee already has a login account.",
            )

    try:
        hashed_password = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hashed_password,
        role=payload.role,
        employee_id=payload.employee_id,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user
