from fastapi import APIRouter, Header
from pydantic import BaseModel
import httpx

router = APIRouter()

class TokenRequest(BaseModel):
  token: str | None = None

@router.post("/github/test-token")
async def test_github_token(body: TokenRequest, authorization: str | None = Header(None)):
  token = body.token
  if not token and authorization and authorization.startswith("Bearer "):
    token = authorization.split(" ")[1]
  if not token:
    return {"ok": False, "error": "No token provided"}

  async with httpx.AsyncClient() as client:
    # Try token scheme first
    resp = await client.get(
      "https://api.github.com/user",
      headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    )
    if resp.status_code == 401:
      # Retry with Bearer
      resp = await client.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
      )
    scopes = resp.headers.get("x-oauth-scopes", "")
    limit = resp.headers.get("x-ratelimit-limit")
    remaining = resp.headers.get("x-ratelimit-remaining")
    reset = resp.headers.get("x-ratelimit-reset")
    if resp.status_code == 200:
      data = resp.json()
      return {
        "ok": True,
        "login": data.get("login"),
        "name": data.get("name"),
        "scopes": [s.strip() for s in scopes.split(',') if s.strip()],
        "rate": {"limit": limit, "remaining": remaining, "reset": reset},
      }
    return {"ok": False, "status": resp.status_code, "error": resp.text}

