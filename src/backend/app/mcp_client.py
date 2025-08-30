"""
MCP Client for GitHub Copilot integration via Model Context Protocol.

This module provides a client for connecting to the GitHub MCP server
and calling the GitHub Copilot coding agent tools.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import httpx
import asyncio

logger = logging.getLogger(__name__)


class GitHubMCPClient:
    """Client for interacting with GitHub MCP server and Copilot coding agent."""
    
    def __init__(self, auth_method: str = "oauth", github_token: Optional[str] = None):
        """
        Initialize the GitHub MCP client.
        
        Args:
            auth_method: Authentication method ("oauth")
            github_token: GitHub OAuth token
        """
        self.auth_method = auth_method
        self.github_token = github_token
        self.server_url = "https://api.githubcopilot.com/mcp/x/copilot"
        self.session: Optional[ClientSession] = None
        
        if not self.github_token:
            raise ValueError("GitHub token is required for authentication")
    
    async def connect(self) -> bool:
        """
        Connect to the GitHub MCP server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.auth_method == "pat":
                headers = {
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json",
                    "X-MCP-Toolsets": "copilot"
                }
                
                logger.info(f"Connecting to GitHub MCP server at {self.server_url}")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.server_url,
                        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                        headers=headers,
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        logger.info("Successfully connected to GitHub MCP server")
                        return True
                    else:
                        logger.error(f"Failed to connect: HTTP {response.status_code} - {response.text}")
                        return False
                        
            elif self.auth_method == "oauth":
                logger.warning("OAuth authentication not yet implemented")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to GitHub MCP server: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the GitHub MCP server.
        
        Returns:
            List of available tools
        """
        try:
            if self.auth_method == "pat":
                headers = {
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json",
                    "X-MCP-Toolsets": "copilot"
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.server_url,
                        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                        headers=headers,
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "result" in result and "tools" in result["result"]:
                            return result["result"]["tools"]
                        else:
                            logger.error(f"Unexpected response format: {result}")
                            return []
                    else:
                        logger.error(f"Failed to list tools: HTTP {response.status_code} - {response.text}")
                        return []
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []
    
    async def create_pull_request_with_copilot(
        self,
        owner: str,
        repo: str,
        problem_statement: str,
        title: str,
        base_ref: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a pull request using GitHub Copilot coding agent.
        
        Args:
            owner: Repository owner
            repo: Repository name
            problem_statement: Description of the problem to solve
            title: Pull request title
            base_ref: Base branch reference (default: "main")
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            if not await self.connect():
                raise Exception("Failed to connect to GitHub MCP server")
            
            params = {
                "owner": owner,
                "repo": repo,
                "problem_statement": problem_statement,
                "title": title,
                "base_ref": base_ref
            }
            
            logger.info(f"Calling create_pull_request_with_copilot for {owner}/{repo}")
            
            if self.auth_method == "pat":
                headers = {
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json",
                    "X-MCP-Toolsets": "copilot"
                }
                
                async with httpx.AsyncClient() as client:
                    mcp_request = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": "create_pull_request_with_copilot",
                            "arguments": params
                        }
                    }
                    response = await client.post(
                        self.server_url,
                        json=mcp_request,
                        headers=headers,
                        timeout=60.0  # Longer timeout for PR creation
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"Successfully created PR: {result}")
                        return result
                    else:
                        error_msg = f"Failed to create PR: HTTP {response.status_code}"
                        logger.error(error_msg)
                        return {"error": error_msg, "status_code": response.status_code}
            
        except Exception as e:
            error_msg = f"Error creating pull request with Copilot: {e}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    async def disconnect(self):
        """Disconnect from the GitHub MCP server."""
        if self.session:
            try:
                await self.session.close()
                self.session = None
                logger.info("Disconnected from GitHub MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")


def create_github_mcp_client(
    auth_method: str = "oauth",
    github_token: Optional[str] = None
) -> GitHubMCPClient:
    """
    Factory function to create a GitHub MCP client.
    
    Args:
        auth_method: Authentication method ("oauth")
        github_token: GitHub OAuth token
        
    Returns:
        GitHubMCPClient instance
    """
    return GitHubMCPClient(auth_method=auth_method, github_token=github_token)
