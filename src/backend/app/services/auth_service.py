import os
import httpx
from typing import Dict, Any, List
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GITHUB_REDIRECT_URI")
    
    def get_github_auth_url(self) -> Dict[str, str]:
        if not self.client_id:
            raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID environment variable is required")
        if not self.redirect_uri:
            raise HTTPException(status_code=500, detail="GITHUB_REDIRECT_URI environment variable is required")
        
        scope = "repo,workflow,admin:repo_hook,public_repo"
        auth_url = f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope}"
        return {"auth_url": auth_url}
    
    async def handle_github_callback(self, code: str) -> Dict[str, Any]:
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code provided")
        
        if not self.client_id:
            raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID environment variable is required")
        if not self.client_secret:
            raise HTTPException(status_code=500, detail="GITHUB_CLIENT_SECRET environment variable is required")
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=400, detail="No access token received")
            
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user information")
            
            user_data = user_response.json()
            
            return {
                "access_token": access_token,
                "user": {
                    "login": user_data["login"],
                    "name": user_data.get("name"),
                    "avatar_url": user_data["avatar_url"]
                }
            }
    
    async def get_user_repositories(self, token: str, limit: int = 10, sort: str = "updated",
                                  direction: str = "desc", page: int = 1) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                },
                params={
                    "sort": sort,
                    "direction": direction,
                    "per_page": limit,
                    "page": page,
                },
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch repositories")

            return response.json()
    
    async def search_user_repositories(self, token: str, query: str, limit: int = 10,
                                     sort: str = "updated", order: str = "desc", page: int = 1) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if user_resp.status_code != 200:
                raise HTTPException(status_code=user_resp.status_code, detail="Failed to fetch user info")

            login = user_resp.json().get("login")
            if not login:
                raise HTTPException(status_code=400, detail="Could not determine user login")

            search_query = f"{query} user:{login} in:name,description,readme"

            search_resp = await client.get(
                "https://api.github.com/search/repositories",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                },
                params={
                    "q": search_query,
                    "per_page": limit,
                    "sort": sort,
                    "order": order,
                    "page": page,
                },
            )

            if search_resp.status_code != 200:
                raise HTTPException(status_code=search_resp.status_code, detail="Failed to search repositories")

            data = search_resp.json()
            return data.get("items", [])
