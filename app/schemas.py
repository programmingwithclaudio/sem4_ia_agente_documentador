from datetime import datetime
from typing import Optional, List
from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, field_validator



# Schemas de FastAPI Users (extendidos)

class UserRead(schemas.BaseUser[int]):
    """Schema para leer usuarios"""
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[str] = []
    
    # 🔧 VALIDADOR PARA CONVERTIR ROLES A STRINGS
    @field_validator('roles', mode='before')
    @classmethod
    def convert_roles_to_strings(cls, v):
        """Convierte objetos Role a strings"""
        if not v:
            return []
        
        # Si ya son strings, retornar tal cual
        if isinstance(v, list) and all(isinstance(item, str) for item in v):
            return v
        
        # Si son objetos Role, extraer el nombre
        try:
            return [role.name if hasattr(role, 'name') else str(role) for role in v]
        except (AttributeError, TypeError):
            return []
    
    class Config:
        from_attributes = True


class UserCreate(schemas.BaseUserCreate):
    """Schema para crear usuarios"""
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema para actualizar usuarios"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None

# Schemas personalizados adicionales
class RoleCreate(BaseModel):
    """Schema para crear rol"""
    name: str
    description: Optional[str] = None


class RoleRead(BaseModel):
    """Schema para leer rol"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserWithRoles(UserRead):
    """Usuario con detalles completos de roles"""
    roles_detail: List[RoleRead] = []
    
    @field_validator('roles_detail', mode='before')
    @classmethod
    def convert_roles(cls, v):
        """Convierte objetos Role a RoleRead"""
        if not v:
            return []
        
        # Si ya son RoleRead, retornar tal cual
        if isinstance(v, list) and all(isinstance(item, dict) for item in v):
            return v
        
        # Si son objetos Role, convertir
        try:
            return [
                {
                    'id': role.id,
                    'name': role.name,
                    'description': role.description
                }
                for role in v
            ]
        except (AttributeError, TypeError):
            return []


class AssignRoleRequest(BaseModel):
    """Request para asignar rol a usuario"""
    user_id: int
    role_name: str


class LoginResponse(BaseModel):
    """Respuesta de login exitoso"""
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class PaginatedUsers(BaseModel):
    """Respuesta paginada de usuarios"""
    items: List[UserRead]
    total: int
    page: int
    size: int
    pages: int


class ChangePasswordRequest(BaseModel):
    """Request para cambiar contraseña"""
    current_password: str
    new_password: str


class UserSessionRead(BaseModel):
    """Schema para leer sesión de usuario"""
    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_type: Optional[str]
    created_at: datetime
    last_activity: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Estadísticas de usuario"""
    total_users: int
    verified_users: int
    active_sessions: int
    users_by_role: dict


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    database: str
    redis: str