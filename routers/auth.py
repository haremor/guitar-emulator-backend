from schemas import PostUser, LoginUser
from utils.password import secure_pwd, verify_pwd
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from db.db import get_file_db, get_main_db
from utils.auth import create_access_token, create_refresh_token, JWTBearer, decodeJWT
from db.models import User, MidiMetadata, MidiFile
from uuid import uuid4

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register_user(data: PostUser, db: Session = Depends(get_main_db), response: Response = None):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    new_user = User(
        id=uuid4(),
        username=data.username,
        email=data.email,
        password=secure_pwd(data.password),
        role=data.role if data.role else "user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user.email, new_user.role.value)
    refresh_token = create_refresh_token(new_user.email)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="None"
    )

    return {"access_token": access_token, "detail": "User registered successfully"}

@router.post("/login")
async def login(data: LoginUser, db: Session = Depends(get_main_db), response: Response = None):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_pwd(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(user.email, user.role.value)
    refresh_token = create_refresh_token(user.email)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="None"
    )

    return {"access_token": access_token, "detail": "Login successful"}

@router.post("/refresh-token")
async def refresh_access_token(refresh_token: str, db: Session = Depends(get_main_db), response: Response = None):
    payload = decodeJWT(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_access_token = create_access_token(user.email, user.role.value)

    return {"access_token": new_access_token, "detail": "Access token refreshed successfully"}

@router.get("/user", dependencies=[Depends(JWTBearer())])
async def get_user_data(db: Session = Depends(get_main_db), token: str = Depends(JWTBearer())):
    payload = decodeJWT(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email
    }

@router.delete("/delete-user/{user_id}")
async def delete_user_and_files(user_id: str, db: Session = Depends(get_main_db), file_db: Session = Depends(get_file_db)):
    # Find the user in the main database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Find all metadata entries for the user
    midi_metadata = db.query(MidiMetadata).filter(MidiMetadata.user_id == user_id).all()

    # Delete the associated files from the file database
    for metadata in midi_metadata:
        file = file_db.query(MidiFile).filter(MidiFile.id == metadata.file_id).first()
        if file:
            file_db.delete(file)
            file_db.commit()

    # Delete the user (this will also delete metadata due to cascade)
    db.delete(user)
    db.commit()

    return {"detail": "User and their MIDI files deleted successfully"}