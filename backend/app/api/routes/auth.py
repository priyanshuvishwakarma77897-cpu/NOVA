
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from backend.app.core.dependencies import get_current_user
from backend.app.database.session import get_db
from backend.app.models import User
from backend.app.schemas.auth import InitialSetupRequest
from backend.app.core.security import hash_password
from datetime import timedelta
from backend.app.services.auth.session_manager import revoke_session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.core.security import verify_password
from backend.app.core.config import settings
from backend.app.schemas.auth import LoginRequest
from backend.app.services.auth.session_manager import create_session

router = APIRouter()


@router.post("/setup", status_code=status.HTTP_201_CREATED)
def initial_setup(
    data: InitialSetupRequest,
    db: Session = Depends(get_db),
):
    with db.begin():
        # Prevent simultaneous setup requests.
        db.execute(text("SELECT pg_advisory_xact_lock(782341)"))

        existing_user = db.scalar(
            select(func.count()).select_from(User)
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Initial account has already been created.",
            )

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
        )

        db.add(user)
        db.flush()

        return {
            "message": "Initial account created successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.username == data.username)
    )

    if user is None or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token, session = create_session(db, user.id)

    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.SESSION_TTL_HOURS * 3600,
    }

@router.get("/me")
def get_owner_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "authenticated": True,
    }


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer()
    ),
    db: Session = Depends(get_db),
):
    revoked = revoke_session(db, credentials.credentials)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    db.commit()

    return {
        "message": "Successfully logged out."
    }