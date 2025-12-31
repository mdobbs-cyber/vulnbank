from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime
import models
from database import engine, get_db
import logging
from pythonjsonlogger import jsonlogger
import sys
import redis

# Logging Config
logger = logging.getLogger()
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Redis for Ban Hammer
redis_client = redis.Redis(host='redis', port=6379, db=0)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.middleware("http")
async def blacklist_middleware(request: Request, call_next):
    client_ip = request.client.host
    logger.info(f"Incoming Request: {request.method} {request.url.path} from {client_ip}")
    if redis_client.exists(f"blacklist:{client_ip}"):
        logger.warning(f"Banned IP attempted access: {client_ip}")
        return JSONResponse(status_code=403, content={"detail": "Access Denied: IP Banned"})
    return await call_next(request)

# SECURITY MISCONFIGURATION: Hardcoded Secret
SECRET_KEY = "vulnerable_bank_secret_123"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False # VULNERABILITY: Mass Assignment exposed here

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        logger.warning(f"Registration failed: Username {user.username} already exists")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # VULNERABILITY: Mass Assignment - directly using user-provided is_admin
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username, 
        password_hash=hashed_password,
        is_admin=user.is_admin 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User registered: {user.username} (Admin: {db_user.is_admin})")
    return {"message": "User created successfully", "is_admin": db_user.is_admin}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # VULNERABILITY: Weak Token generation (No expiration enforcement in this simple example, plus hardcoded secret)
    access_token = create_access_token(data={"sub": user.username, "admin": user.is_admin})
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def read_root():
    return {"message": "Auth Service Ready"}
