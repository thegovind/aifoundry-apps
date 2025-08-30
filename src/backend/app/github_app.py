import os
import jwt
import time
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class GitHubAppClient:
    def __init__(self):
        self.app_id = os.getenv("GITHUB_APP_ID", "1866067")
        self.client_id = os.getenv("GITHUB_CLIENT_ID", "Iv23liJ8gCLvAnruP9KV")
        self.private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH", "/home/ubuntu/attachments/c88b6cde-e965-426e-9bbd-3ac7433d9557/aifoundry-app.2025-08-29.private-key.pem")
        
    def generate_jwt_token(self) -> str:
        """Generate JWT token for GitHub App authentication"""
        with open(self.private_key_path, 'r') as key_file:
            private_key = key_file.read()
        
        now = int(time.time())
        payload = {
            'iat': now - 60,
            'exp': now + (10 * 60),
            'iss': self.app_id
        }
        
        return jwt.encode(payload, private_key, algorithm='RS256')
    
    async def get_installation_token(self, installation_id: str) -> str:
        """Get installation access token for a specific installation"""
        jwt_token = self.generate_jwt_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 201:
                return response.json()["token"]
            else:
                raise HTTPException(status_code=response.status_code, detail=f"Failed to get installation token: {response.text}")
    
    async def fork_repository(self, installation_token: str, owner: str, repo: str, new_owner: str) -> Dict[str, Any]:
        """Fork a repository to the authenticated user's account"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/forks",
                headers={
                    "Authorization": f"token {installation_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if response.status_code == 202:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=f"Failed to fork repository: {response.text}")
