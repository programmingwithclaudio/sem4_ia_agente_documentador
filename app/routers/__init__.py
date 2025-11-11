#app\routers\__init__.py
from .users import router as users_router
from .roles import router as roles_router
from .admin import router as admin_router
from .health import router as health_router

__all__ = ["users_router", "roles_router", "admin_router", "health_router"]