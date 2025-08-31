from fastapi import APIRouter, Depends, Header
from typing import Dict, Any
from ...services.auth_service import AuthService
from ...api.dependencies import get_auth_service

router = APIRouter()

@router.get("/github")
async def github_oauth_login(auth_service: AuthService = Depends(get_auth_service)):
    """Initiate GitHub OAuth flow"""
    return auth_service.get_github_auth_url()

@router.post("/github/callback")
async def github_oauth_callback(request: Dict[str, str], auth_service: AuthService = Depends(get_auth_service)):
    """Handle GitHub OAuth callback"""
    code = request.get("code")
    return await auth_service.handle_github_callback(code)
