from fastapi import APIRouter, Depends, Header, Query, HTTPException
from typing import List, Dict, Any
import httpx
from ...services.auth_service import AuthService
from ...api.dependencies import get_auth_service, get_agent_service

router = APIRouter()

@router.get("/repositories")
async def get_user_repositories(
    authorization: str = Header(...),
    limit: int = Query(10, ge=1, le=100, description="Number of most recent repositories to return"),
    sort: str = Query("updated", description="Sort field: created, updated, pushed, full_name"),
    direction: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user's most recent repositories."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    return await auth_service.get_user_repositories(token, limit, sort, direction, page)

@router.get("/repositories/search")
async def search_user_repositories(
    q: str = Query(..., min_length=1, description="Search text for repository name/description"),
    authorization: str = Header(...),
    limit: int = Query(10, ge=1, le=100, description="Max number of results to return"),
    sort: str = Query("updated", description="Sort: stars, forks, help-wanted-issues, updated"),
    order: str = Query("desc", description="Order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Search within the authenticated user's repositories by name/description."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    return await auth_service.search_user_repositories(token, q, limit, sort, order, page)

@router.get("/assignments")
async def get_user_assignments(
    authorization: str = Header(...),
    agent_service = Depends(get_agent_service)
):
    """Get user's agent assignments for dashboard"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=user_resp.status_code, detail="Failed to get user info")
        
        user_id = str(user_resp.json()["id"])
        return await agent_service.get_user_assignments(user_id)

@router.get("/assignments/{assignment_id}")
async def get_assignment_details(
    assignment_id: str,
    authorization: str = Header(...),
    agent_service = Depends(get_agent_service)
):
    """Get detailed assignment information including markdown context"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ")[1]
    
    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=user_resp.status_code, detail="Failed to get user info")
        
        user_id = str(user_resp.json()["id"])
        return await agent_service.get_assignment_details(assignment_id, user_id)
