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
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        # GITHUB_PRIVATE_KEY_PATH can be either a file path or the PEM content
        private_key_input = os.getenv("GITHUB_PRIVATE_KEY_PATH")
        self.private_key: Optional[str] = None

        if not self.app_id:
            raise ValueError("GITHUB_APP_ID environment variable is required")
        if not self.client_id:
            raise ValueError("GITHUB_CLIENT_ID environment variable is required")
        if not private_key_input:
            raise ValueError("GITHUB_PRIVATE_KEY_PATH environment variable is required")

        # Resolve private key from file path or direct PEM
        try:
            if os.path.exists(private_key_input):
                with open(private_key_input, 'r') as key_file:
                    self.private_key = key_file.read()
            else:
                # If it looks like PEM content, use it directly
                if private_key_input.strip().startswith("-----BEGIN"):
                    self.private_key = private_key_input
                else:
                    # Last attempt: try opening as path anyway to surface clear error
                    with open(private_key_input, 'r') as key_file:
                        self.private_key = key_file.read()
        except Exception as e:
            raise ValueError(f"Failed to load GitHub private key from GITHUB_PRIVATE_KEY_PATH: {e}")
        
    def generate_jwt_token(self) -> str:
        """Generate JWT token for GitHub App authentication"""
        if not self.private_key:
            raise ValueError("GitHub private key not loaded")
        
        now = int(time.time())
        payload = {
            'iat': now - 60,
            'exp': now + (10 * 60),
            'iss': self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
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
