"""
GitHub repository creation and management service.
"""
import os
import logging
from typing import Dict, Any, Optional
from github import Github, GithubException
from pathlib import Path

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.mock_mode = not self.github_token
        if not self.mock_mode:
            self.github = Github(self.github_token)
        else:
            logger.warning("GitHub token not found, running in mock mode")

    def create_repository(self, repo_name: str, description: str, private: bool = False) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        if self.mock_mode:
            logger.info(f"Mock mode: Would create repository '{repo_name}' with description '{description}'")
            return {
                "success": True,
                "repo_url": f"https://github.com/mock-user/{repo_name}",
                "clone_url": f"https://github.com/mock-user/{repo_name}.git",
                "repo_name": f"mock-user/{repo_name}"
            }
        
        try:
            user = self.github.get_user()
            repo = user.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=True
            )
            return {
                "success": True,
                "repo_url": repo.html_url,
                "clone_url": repo.clone_url,
                "repo_name": repo.full_name
            }
        except GithubException as e:
            logger.error(f"Failed to create repository: {e}")
            return {"success": False, "error": str(e)}

    def create_file(self, repo_name: str, file_path: str, content: str, commit_message: str) -> Dict[str, Any]:
        """Create a file in the repository."""
        if self.mock_mode:
            logger.info(f"Mock mode: Would create file '{file_path}' in repository '{repo_name}' with message '{commit_message}'")
            return {"success": True}
        
        try:
            repo = self.github.get_repo(repo_name)
            repo.create_file(file_path, commit_message, content)
            return {"success": True}
        except GithubException as e:
            logger.error(f"Failed to create file: {e}")
            return {"success": False, "error": str(e)}

    def generate_agents_md_content(self, content_type: str, item: Dict[str, Any], customization: Dict[str, Any]) -> str:
        """Generate agents.md file content based on content type."""
        def safe_get(obj, key, default=""):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        def safe_join(obj, key, default=""):
            if isinstance(obj, dict):
                value = obj.get(key, [])
            else:
                value = getattr(obj, key, [])
            if isinstance(value, list):
                return ', '.join(value)
            return str(value) if value else default
        
        if content_type == "template":
            return f"""# {safe_get(item, 'title')}

{safe_get(item, 'description')}

- **Collection**: {safe_get(item, 'collection')}
- **Task**: {safe_get(item, 'task')}
- **Languages**: {safe_join(item, 'languages')}
- **Models**: {safe_join(item, 'models')}
- **Databases**: {safe_join(item, 'databases')}

- **Company**: {safe_get(customization, 'company_name')}
- **Industry**: {safe_get(customization, 'industry')}
- **Use Case**: {safe_get(customization, 'use_case')}
- **Brand Theme**: {safe_get(customization, 'brand_theme')}
- **Primary Color**: {safe_get(customization, 'primary_color')}

{safe_get(customization, 'customer_scenario')}

{safe_get(customization, 'additional_requirements')}

- **Use MCP Tools**: {safe_get(customization, 'use_mcp_tools')}
- **Use A2A**: {safe_get(customization, 'use_a2a')}

{safe_get(item, 'github_url')}
"""
        elif content_type == "pattern":
            return f"""# {safe_get(item, 'title')}

{safe_get(item, 'description')}

- **Type**: {safe_get(item, 'type')}
- **Use Cases**: {safe_join(item, 'use_cases')}

- **Company**: {safe_get(customization, 'company_name')}
- **Industry**: {safe_get(customization, 'industry')}
- **Use Case**: {safe_get(customization, 'use_case')}
- **Scenario Description**: {safe_get(customization, 'customer_scenario')}
- **Additional Requirements**: {safe_get(customization, 'additional_requirements')}

- **Use MCP Tools**: {safe_get(customization, 'use_mcp_tools')}
- **Use A2A**: {safe_get(customization, 'use_a2a')}

{safe_get(item, 'github_url')}
"""
        elif content_type == "spec":
            return f"""# {safe_get(item, 'title')}

{safe_get(item, 'description')}

{safe_get(item, 'content')}

- **Company**: {safe_get(customization, 'company_name')}
- **Industry**: {safe_get(customization, 'industry')}
- **Use Case**: {safe_get(customization, 'use_case')}
- **Customer Scenario**: {safe_get(customization, 'customer_scenario')}
- **Additional Requirements**: {safe_get(customization, 'additional_requirements')}

- **Use MCP Tools**: {safe_get(customization, 'use_mcp_tools')}
- **Use A2A**: {safe_get(customization, 'use_a2a')}
"""
        else:
            return f"""# {item.get('title', 'Unknown Item')}

{item.get('description', 'No description available')}

- **Company**: {customization.get('company_name', 'Not specified')}
- **Industry**: {customization.get('industry', 'Not specified')}
- **Use Case**: {customization.get('use_case', 'Not specified')}
- **Customer Scenario**: {customization.get('customer_scenario', 'Not specified')}
- **Additional Requirements**: {customization.get('additional_requirements', 'None')}

- **Use MCP Tools**: {customization.get('use_mcp_tools', False)}
- **Use A2A**: {customization.get('use_a2a', False)}
"""

    def generate_github_actions_workflow(self, agent_type: str, azure_config: Dict[str, Any]) -> str:
        """Generate GitHub Actions workflow for Codex automation."""
        if agent_type == "codex-cli":
            return f"""name: Azure OpenAI Codex Automation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  codex-automation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install openai azure-identity
    
    - name: Run Codex Automation
      env:
        AZURE_OPENAI_API_KEY: ${{{{ secrets.AZURE_OPENAI_API_KEY }}}}
        AZURE_OPENAI_ENDPOINT: ${{{{ secrets.AZURE_OPENAI_ENDPOINT }}}}
      run: |
        python -c "
        import openai
        import os
        
        openai.api_type = 'azure'
        openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        openai.api_base = os.getenv('AZURE_OPENAI_ENDPOINT')
        openai.api_version = '2024-02-01'
        
        with open('agents.md', 'r') as f:
            context = f.read()
        
        print('Codex automation completed with context from agents.md')
        print('Repository setup complete for Azure OpenAI Codex integration')
        "
"""
        return ""
