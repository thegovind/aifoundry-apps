from functools import lru_cache
from ..services.template_service import TemplateService
from ..services.spec_service import SpecService
from ..services.auth_service import AuthService
from ..services.agent_service import AgentService
from ..cosmos_service import CosmosService
from ..github_app import GitHubAppClient
from ..core.config import settings

@lru_cache()
def get_template_service() -> TemplateService:
    return TemplateService()

@lru_cache()
def get_spec_service() -> SpecService:
    return SpecService()

@lru_cache()
def get_auth_service() -> AuthService:
    return AuthService()

@lru_cache()
def get_agent_service() -> AgentService:
    return AgentService()

@lru_cache()
def get_cosmos_service() -> CosmosService:
    return CosmosService()

def get_github_app_client() -> GitHubAppClient:
    try:
        return GitHubAppClient()
    except ValueError:
        return None
