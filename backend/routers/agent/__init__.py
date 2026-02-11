from fastapi import APIRouter, Depends

# Import the routers from your files
from .agent import router as agent_router


# Create one master Agent router
agent_master_router = APIRouter(prefix="/api/agent", tags=["Agent"])

# Include the sub-functionality routers
agent_master_router.include_router(agent_router, prefix="", tags=["Agent"])
