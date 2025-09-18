import os
import sys
import types
import pytest
from fastapi.testclient import TestClient

# Ensure we don't accidentally load real credentials from a local .env
os.environ.setdefault("COSMOS_CONNECTION_STRING", "")
os.environ.setdefault("AZURE_OPENAI_KEY", "")

# Provide lightweight stubs for Azure SDKs if not installed, to avoid ImportError during app import
try:  # pragma: no cover - import guard
    import azure.cosmos  # type: ignore
    import azure.identity  # type: ignore
except Exception:  # pragma: no cover - only in minimal test envs
    azure_module = types.ModuleType("azure")
    cosmos_module = types.ModuleType("azure.cosmos")
    cosmos_exc_module = types.ModuleType("azure.cosmos.exceptions")
    identity_module = types.ModuleType("azure.identity")

    class _Dummy:
        def __getattr__(self, *_):
            return self
        def __call__(self, *_, **__):
            return self

    class CosmosClient:  # minimal stub
        def __init__(self, *_, **__):
            pass
        @classmethod
        def from_connection_string(cls, *_, **__):
            return cls()
        def create_database_if_not_exists(self, *_, **__):
            return _Dummy()
        def get_database_client(self, *_, **__):
            return _Dummy()

    class PartitionKey:
        def __init__(self, *_, **__):
            pass

    class CosmosResourceNotFoundError(Exception):
        pass

    class DefaultAzureCredential:  # identity stub
        def __init__(self, *_, **__):
            pass

    cosmos_module.CosmosClient = CosmosClient
    cosmos_module.PartitionKey = PartitionKey
    cosmos_exc_module.CosmosResourceNotFoundError = CosmosResourceNotFoundError
    identity_module.DefaultAzureCredential = DefaultAzureCredential

    sys.modules.setdefault("azure", azure_module)
    sys.modules.setdefault("azure.cosmos", cosmos_module)
    sys.modules.setdefault("azure.cosmos.exceptions", cosmos_exc_module)
    sys.modules.setdefault("azure.identity", identity_module)

from app.main import app
from app.api.dependencies import get_auth_service


class _FakeAuthService:
    def get_github_auth_url(self):
        # Return a deterministic URL for tests without requiring env vars
        return {"auth_url": "https://github.com/login/oauth/authorize?client_id=fake&redirect_uri=http://localhost/callback&scope=repo"}

    async def handle_github_callback(self, code: str):
        # Minimal fake response
        return {
            "access_token": "fake_token",
            "user": {"login": "tester", "name": "Test User", "avatar_url": "http://example/avatar.png"},
        }


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    return TestClient(app)
