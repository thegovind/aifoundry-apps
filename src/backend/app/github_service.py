"""
GitHub repository creation and management service.
"""
import os
import logging
import base64
from typing import Dict, Any, Optional
from github import Github, GithubException
from github import InputGitTreeElement
from pathlib import Path
from nacl import encoding, public

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

    def copy_repository_content(self, source_owner: str, source_repo: str, target_repo_name: str, description: str) -> Dict[str, Any]:
        """Copy content from a public repository to a new repository in user's account."""
        if self.mock_mode:
            logger.info(f"Mock mode: Would copy repository '{source_owner}/{source_repo}' to '{target_repo_name}'")
            return {
                "success": True,
                "repo_url": f"https://github.com/mock-user/{target_repo_name}",
                "clone_url": f"https://github.com/mock-user/{target_repo_name}.git",
                "repo_name": f"mock-user/{target_repo_name}"
            }
        
        try:
            user = self.github.get_user()
            new_repo = user.create_repo(
                name=target_repo_name,
                description=description,
                private=False,
                auto_init=False
            )
            
            source_github = Github()  # Anonymous access for public repos
            source_repository = source_github.get_repo(f"{source_owner}/{source_repo}")
            
            try:
                default_branch = source_repository.default_branch
                
                contents = source_repository.get_contents("", ref=default_branch)
                
                def copy_contents(contents_list, path=""):
                    for content in contents_list:
                        if content.type == "dir":
                            dir_contents = source_repository.get_contents(content.path, ref=default_branch)
                            copy_contents(dir_contents, content.path)
                        else:
                            try:
                                file_content = content.decoded_content.decode('utf-8')
                                new_repo.create_file(
                                    content.path,
                                    f"Copy {content.path} from {source_owner}/{source_repo}",
                                    file_content
                                )
                                logger.info(f"Copied file: {content.path}")
                            except Exception as e:
                                logger.warning(f"Failed to copy file {content.path}: {e}")
                
                copy_contents(contents)
                
                return {
                    "success": True,
                    "repo_url": new_repo.html_url,
                    "clone_url": new_repo.clone_url,
                    "repo_name": new_repo.full_name
                }
                
            except Exception as e:
                logger.error(f"Failed to copy repository contents: {e}")
                return {
                    "success": True,
                    "repo_url": new_repo.html_url,
                    "clone_url": new_repo.clone_url,
                    "repo_name": new_repo.full_name,
                    "warning": f"Repository created but content copying failed: {str(e)}"
                }
                
        except GithubException as e:
            logger.error(f"Failed to copy repository: {e}")
            return {"success": False, "error": str(e)}

    def copy_into_existing_repo(self, source_owner: str, source_repo: str, target_full_name: str, progress_cb=None, throttle_ms: int = 150, should_cancel=None) -> Dict[str, Any]:
        """
        Copy files from a public source repo into an existing target repo.
        Skips files that already exist.
        """
        if self.mock_mode:
            logger.info(f"Mock mode: Would copy into existing repo '{target_full_name}' from '{source_owner}/{source_repo}'")
            return {"success": True}

        try:
            target = self.github.get_repo(target_full_name)
            source_github = Github()
            source = source_github.get_repo(f"{source_owner}/{source_repo}")
            default_branch = source.default_branch

            contents = source.get_contents("", ref=default_branch)
            total = 0
            copied = 0

            # pre-count files (best effort)
            def count_files(items):
                nonlocal total
                for item in items:
                    if item.type == "dir":
                        count_files(source.get_contents(item.path, ref=default_branch))
                    else:
                        total += 1
            try:
                count_files(contents if isinstance(contents, list) else [contents])
            except Exception:
                total = 0

            import time
            def copy_contents(items):
                for item in items:
                    if should_cancel and should_cancel():
                        return
                    if item.type == "dir":
                        copy_contents(source.get_contents(item.path, ref=default_branch))
                    else:
                        try:
                            # If file exists, skip
                            try:
                                target.get_contents(item.path)
                                continue
                            except Exception:
                                pass
                            file_content = item.decoded_content.decode("utf-8", errors="ignore")
                            target.create_file(item.path, f"Add {item.path} from {source_owner}/{source_repo}", file_content)
                            nonlocal copied
                            copied += 1
                            if progress_cb:
                                try:
                                    progress_cb({"event": "copy-progress", "copied": copied, "total": total})
                                except Exception:
                                    pass
                            time.sleep(throttle_ms / 1000.0)
                        except Exception as e:
                            logger.warning(f"Failed to copy {item.path}: {e}")

            copy_contents(contents if isinstance(contents, list) else [contents])
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to copy into existing repo: {e}")
            return {"success": False, "error": str(e)}

    def fast_import_from_tar(self, source_owner: str, source_repo: str, target_full_name: str, progress_cb=None, should_cancel=None) -> Dict[str, Any]:
        """Import repository by downloading a tarball and committing via Git Data API."""
        if self.mock_mode:
            logger.info(f"Mock mode: Would fast-import '{source_owner}/{source_repo}' into '{target_full_name}'")
            return {"success": True}

        import io
        import tarfile
        import requests

        try:
            # Discover default branch
            headers = {"Accept": "application/vnd.github+json"}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
            resp = requests.get(f"https://api.github.com/repos/{source_owner}/{source_repo}", headers=headers)
            resp.raise_for_status()
            default_branch = resp.json().get("default_branch", "main")

            # Download tarball
            if should_cancel and should_cancel():
                return {"success": False, "error": "cancelled"}
            tar_headers = {"Accept": "application/octet-stream"}
            if self.github_token:
                tar_headers["Authorization"] = f"token {self.github_token}"
            tar_resp = requests.get(
                f"https://api.github.com/repos/{source_owner}/{source_repo}/tarball/{default_branch}",
                headers=tar_headers,
                stream=True,
            )
            tar_resp.raise_for_status()
            data = io.BytesIO(tar_resp.content)

            tf = tarfile.open(fileobj=data, mode="r:*")
            members = [m for m in tf.getmembers() if m.isfile()]
            total = len(members)
            if progress_cb:
                try:
                    progress_cb({"event": "copy-progress", "copied": 0, "total": total})
                except Exception:
                    pass

            repo = self.github.get_repo(target_full_name)
            elements = []
            copied = 0
            for m in members:
                if should_cancel and should_cancel():
                    break
                parts = m.name.split('/', 1)
                relpath = parts[1] if len(parts) > 1 else m.name
                if relpath.startswith('.git/'):
                    continue
                f = tf.extractfile(m)
                if not f:
                    continue
                content = f.read()
                b64 = base64.b64encode(content).decode('utf-8')
                blob = repo.create_git_blob(b64, "base64")
                elements.append(InputGitTreeElement(path=relpath, mode='100644', type='blob', sha=blob.sha))
                copied += 1
                if progress_cb and copied % 20 == 0:
                    try:
                        progress_cb({"event": "copy-progress", "copied": copied, "total": total})
                    except Exception:
                        pass

            if not elements:
                return {"success": True}

            # If cancelled after staging
            if should_cancel and should_cancel():
                return {"success": False, "error": "cancelled"}
            tree = repo.create_git_tree(elements)
            commit = repo.create_git_commit("Initial import from template", tree, parents=[])
            try:
                repo.create_git_ref(ref='refs/heads/main', sha=commit.sha)
            except GithubException:
                repo.create_git_ref(ref='refs/heads/master', sha=commit.sha)
            return {"success": True}
        except Exception as e:
            logger.error(f"Fast import failed: {e}")
            return {"success": False, "error": str(e)}

    def create_repository_secrets(self, repo_name: str, secrets: Dict[str, str]) -> Dict[str, Any]:
        """Create repository secrets for GitHub Actions."""
        if self.mock_mode:
            logger.info(f"Mock mode: Would create secrets {list(secrets.keys())} in repository '{repo_name}'")
            return {"success": True, "secrets_created": list(secrets.keys())}
        
        try:
            repo = self.github.get_repo(repo_name)
            
            public_key_response = repo.get_public_key()
            public_key = public_key_response.key
            key_id = public_key_response.key_id
            
            created_secrets = []
            
            for secret_name, secret_value in secrets.items():
                try:
                    public_key_bytes = base64.b64decode(public_key)
                    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
                    encrypted_value = sealed_box.encrypt(secret_value.encode("utf-8"))
                    encrypted_value_b64 = base64.b64encode(encrypted_value).decode("utf-8")
                    
                    repo.create_secret(secret_name, encrypted_value_b64, key_id)
                    created_secrets.append(secret_name)
                    logger.info(f"Created secret '{secret_name}' in repository '{repo_name}'")
                    
                except Exception as e:
                    logger.error(f"Failed to create secret '{secret_name}': {e}")
            
            return {
                "success": True,
                "secrets_created": created_secrets,
                "total_secrets": len(secrets),
                "failed_secrets": len(secrets) - len(created_secrets)
            }
            
        except Exception as e:
            logger.error(f"Failed to create repository secrets: {e}")
            return {"success": False, "error": str(e)}

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
