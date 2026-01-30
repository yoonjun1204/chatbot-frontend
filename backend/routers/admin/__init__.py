# routers/admin/__init__.py
from fastapi import APIRouter, Depends
from dependencies import require_admin

# Import the routers from your files
from .UserManagement import router as user_management_router
from .LogsAndPerformance import router as logs_performance_router

# Create one master Admin router
admin_master_router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],  # Apply admin dependency to all routes
)

# Include the sub-functionality routers
admin_master_router.include_router(
    user_management_router, prefix="/users", tags=["Admin: Users"]
)

admin_master_router.include_router(
    logs_performance_router, prefix="/logs", tags=["Admin: Logs & Performance"]
)

# You can include more admin-related routers here as needed
