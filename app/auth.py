# app/auth.py
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.models import User, Role, get_db
from app.config import settings
from pydantic import BaseModel

from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi.encoders import jsonable_encoder
from fastapi import Request

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/signin")

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    id: int
    username: str
    email: str
    roles: List[str]

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    roles: Optional[List[str]] = ["ROLE_USER"]


# Utilizamos el método `create_access_token` para crear el token JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = timedelta(hours=settings.jwt_expires_hours)
    
    # Convertir el `timedelta` a segundos para que sea serializable
    expire_seconds = expire.total_seconds()
    
    to_encode.update({"exp": expire_seconds})
    
    # Ahora podemos crear el JWT sin problemas
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm="HS256")
    return encoded_jwt

async def get_jwt_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

async def admin_required(current_user: User = Depends(get_current_user)):
    if not any(role.name == 'ROLE_ADMIN' for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken!"
        )
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use!"
        )
    
    db_user = User(
        username=user.username,
        email=user.email,
        password=user.password
    )
    
    for role_name in user.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            db_user.roles.append(role)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "User registered successfully!"}



@auth_router.post("/signin", response_model=Token)
async def signin(request: Request, db: Session = Depends(get_db)):
    # Verifica el tipo de contenido
    content_type = request.headers.get("Content-Type")
    
    # Si el tipo de contenido es JSON
    if "application/json" in content_type:
        # Extrae los datos del cuerpo de la solicitud como JSON
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    
    # Si el tipo de contenido es form-urlencoded
    elif "application/x-www-form-urlencoded" in content_type:
        # Extrae los datos del formulario
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
    
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported Media Type. Use either application/json or application/x-www-form-urlencoded."
        )
    
    # Verifica si los campos están presentes
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required."
        )
    
    # Busca al usuario en la base de datos
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.check_password(password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Genera el token JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    # Prepara la respuesta con los detalles del usuario
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "roles": [role.name for role in user.roles]
    }

    # Crea la respuesta JSON con los detalles del usuario
    response = JSONResponse(content=jsonable_encoder(response_data))
    
    # Establecemos la cookie con el token de acceso
    response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,  # La cookie solo es accesible desde el servidor (no por JavaScript)
        max_age=timedelta(hours=settings.jwt_expires_hours),  # Duración de la cookie
        expires=timedelta(hours=settings.jwt_expires_hours),  # Duración de la cookie
        secure=True,  # Habilitar solo en HTTPS
        samesite="Strict"  # Estrictamente solo en el mismo sitio
    )
    
    return response

@auth_router.post("/signout")
async def signout(response: Response):
    # Eliminar la cookie del token JWT
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}

@auth_router.get("/protected")
async def protected_route(token: str = Depends(get_jwt_from_cookie)):
    # Decodifica el token y valida el usuario...
    pass