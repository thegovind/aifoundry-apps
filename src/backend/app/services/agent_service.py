import os
import re
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from ..models.schemas import SWEAgentRequest, CustomizationRequest
from ..github_service import GitHubService
from ..progress import broker
from ..cosmos_service import CosmosService
from ..core.config import settings

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.cosmos_service = CosmosService()
    
    async def assign_to_swe_agent(self, template_id: str, request: SWEAgentRequest, 
                                templates_data: List, patterns_data: List, specs_data: List,
                                authorization: Optional[str] = None,
                                progress_job: Optional[str] = None) -> Dict[str, Any]:
        logger.debug(f"Looking for template_id: {template_id}")
        template = next((t for t in templates_data if t.id == template_id), None)
        pattern = None
        if not template:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
        
        if request.agent_id == "devin":
            item = template if template else pattern
            item_type = "template" if template else "pattern"
            
            # Resolve GitHub token: prefer valid Bearer header, else request.github_token
            gh_token: Optional[str] = None
            if authorization and authorization.startswith("Bearer "):
                candidate = authorization.split(" ")[1]
                # Accept known GitHub token prefixes; otherwise ignore (could be Devin API key)
                if any(candidate.startswith(p) for p in ("gho_", "ghu_", "ghs_", "ghp_", "github_pat_")):
                    gh_token = candidate
            if not gh_token and request.github_token:
                gh_token = request.github_token
            if not gh_token:
                raise HTTPException(status_code=401, detail="GitHub authentication required (missing or invalid token)")

            repo_url = getattr(item, 'github_url', item.get('github_url', '') if isinstance(item, dict) else '')
            match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
            if not match:
                raise HTTPException(status_code=400, detail=f"Could not extract owner/repo from URL: {repo_url}")
            src_owner, src_repo = match.groups()

            title = getattr(item, 'title', item.get('title', 'template') if isinstance(item, dict) else 'template')
            safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', title.lower())
            company = request.customization.company_name or "customer"
            company_safe = re.sub(r'[^a-zA-Z0-9-]', '-', company.lower()).strip('-') or 'customer'
            target_repo = f"{safe_name}-{company_safe}"

            # Determine target owner/repo and try fork first; fallback to import if forbidden
            if progress_job:
                await broker.publish(progress_job, "resolve-source", {"repo_url": repo_url})
            # Discover user login and target owner
            async with httpx.AsyncClient() as client:
                user_resp = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {gh_token}"}
                )
                if user_resp.status_code != 200:
                    raise HTTPException(status_code=user_resp.status_code, detail="Failed to identify GitHub user")
                user_login = user_resp.json().get("login")

            target_owner = (request.customization.owner or "").strip() or user_login
            desired_repo_name = (request.customization.repo or "").strip() or target_repo

            # Use GitHub App installation token for repo writes
            # Choose token for write operations
            # 1) Prefer explicit personal access token if provided (best for personal account ops)
            write_token = request.github_pat or gh_token
            install_token: Optional[str] = None
            try:
                from ..github_app import GitHubAppClient
                app_client = GitHubAppClient()
                install_token = await app_client.get_installation_token_for_owner(target_owner)
                write_token = install_token or gh_token
            except Exception as e:
                logger.info(f"Proceeding without GitHub App installation token for owner '{target_owner}': {e}")

            fork_ok = False
            final_repo_name = desired_repo_name
            created_repo = False

            async with httpx.AsyncClient() as client:
                # Attempt to fork (organization if owner differs)
                fork_body = {}
                if target_owner and target_owner != user_login:
                    fork_body["organization"] = target_owner
                # Optionally skip fork if user prefers import/copy
                if request.prefer_import:
                    fork_resp = httpx.Response(status_code=418)  # sentinel to skip fork flow
                else:
                    if progress_job:
                        await broker.publish(progress_job, "fork-start", {"source": f"{src_owner}/{src_repo}", "target_owner": target_owner})
                    fork_resp = await client.post(
                        f"https://api.github.com/repos/{src_owner}/{src_repo}/forks",
                        headers={
                            "Authorization": f"token {write_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        json=fork_body or None,
                        timeout=30.0,
                    )
                    if fork_resp.status_code == 401 and "Bad credentials" in fork_resp.text:
                        fork_resp = await client.post(
                            f"https://api.github.com/repos/{src_owner}/{src_repo}/forks",
                            headers={
                                "Authorization": f"Bearer {write_token}",
                                "Accept": "application/vnd.github.v3+json",
                            },
                            json=fork_body or None,
                            timeout=30.0,
                        )
                if fork_resp.status_code in (201, 202):
                    fork_ok = True
                    if progress_job:
                        await broker.publish(progress_job, "fork-ok", {"owner": target_owner, "repo": desired_repo_name})
                    final_repo_name = src_repo if desired_repo_name == src_repo else desired_repo_name
                    # Attempt rename if requested different name
                    if desired_repo_name and desired_repo_name != src_repo:
                        rename_resp = await client.patch(
                            f"https://api.github.com/repos/{target_owner}/{src_repo}",
                            headers={
                                "Authorization": f"token {write_token}",
                                "Accept": "application/vnd.github.v3+json",
                            },
                            json={"name": desired_repo_name},
                            timeout=30.0,
                        )
                        if rename_resp.status_code in (200, 201):
                            final_repo_name = desired_repo_name
                        else:
                            final_repo_name = src_repo
                else:
                    fork_ok = False
                    # If using a GitHub App user token (ghu_) and we hit integration restrictions, give actionable error if no PAT provided
                    if fork_resp.status_code in (401, 403) and (gh_token.startswith("ghu_") and not request.github_pat):
                        logger.warning("Fork blocked by integration policy with GitHub App user token; suggest PAT")
                        # Continue to import path which may also fail on repo create; we will raise a clearer message there if needed

                if not fork_ok:
                    # Check if repo already exists
                    if progress_job:
                        await broker.publish(progress_job, "create-start", {"owner": target_owner, "repo": desired_repo_name})
                    get_repo_resp = await client.get(
                        f"https://api.github.com/repos/{target_owner}/{desired_repo_name}",
                        headers={
                            "Authorization": f"token {write_token}",
                            "Accept": "application/vnd.github+json",
                        },
                        timeout=30.0,
                    )
                    if get_repo_resp.status_code == 401 and "Bad credentials" in get_repo_resp.text:
                        get_repo_resp = await client.get(
                            f"https://api.github.com/repos/{target_owner}/{desired_repo_name}",
                            headers={
                                "Authorization": f"Bearer {write_token}",
                                "Accept": "application/vnd.github+json",
                            },
                            timeout=30.0,
                        )
                    repo_exists = get_repo_resp.status_code == 200

                    if not repo_exists:
                        # Create repo as app installation
                        create_repo_endpoint = (
                            f"https://api.github.com/user/repos" if target_owner == user_login
                            else f"https://api.github.com/orgs/{target_owner}/repos"
                        )
                        create_resp = await client.post(
                            create_repo_endpoint,
                            headers={
                                "Authorization": f"token {write_token}",
                                "Accept": "application/vnd.github+json",
                            },
                            json={
                                "name": desired_repo_name,
                                "private": False,
                                "has_issues": True,
                                "has_projects": True,
                                "has_wiki": False,
                                "auto_init": False,
                            },
                            timeout=30.0,
                        )
                        if create_resp.status_code == 401 and "Bad credentials" in create_resp.text:
                            create_resp = await client.post(
                                create_repo_endpoint,
                                headers={
                                    "Authorization": f"Bearer {write_token}",
                                    "Accept": "application/vnd.github+json",
                                },
                                json={
                                    "name": desired_repo_name,
                                    "private": False,
                                    "has_issues": True,
                                    "has_projects": True,
                                    "has_wiki": False,
                                    "auto_init": False,
                                },
                                timeout=30.0,
                            )
                        if create_resp.status_code not in (201,):
                            detail_msg = f"Failed to create repository: {create_resp.text}"
                            if (gh_token.startswith("ghu_") and not request.github_pat) and create_resp.status_code in (401, 403):
                                detail_msg += "; your GitHub token appears to be a GitHub App user token (ghu_). Personal repo creation via API is often blocked for app tokens. Provide a classic Personal Access Token (github_pat_ or ghp_) in the UI and try again, or create the empty repo manually and specify owner/repo."
                            raise HTTPException(status_code=create_resp.status_code, detail=detail_msg)
                        else:
                            created_repo = True

                    # Import/copy contents
                    if progress_job:
                        await broker.publish(progress_job, "populate-start", {"owner": target_owner, "repo": desired_repo_name})

                    # Try fast tarball + Git Data import first (fewest requests)
                    gh_service = GitHubService(github_token=write_token)
                    def should_cancel():
                        from ..progress import broker as _b
                        return _b.is_cancelled(progress_job) if progress_job else False
            fast_result = gh_service.fast_import_from_tar(
                src_owner,
                src_repo,
                f"{target_owner}/{desired_repo_name}",
                progress_cb=lambda p: asyncio.create_task(broker.publish(progress_job, p.get("event","copy-progress"), {"copied": p.get("copied"), "total": p.get("total")})) if progress_job else None,
                should_cancel=should_cancel,
            )
            if fast_result.get("success"):
                if progress_job:
                    await broker.publish(progress_job, "import-ok", {"owner": target_owner, "repo": desired_repo_name})
                final_repo_name = desired_repo_name
            else:
                # If fast import failed due to GitHub API rate limit, advise manual fork
                fr_err = (fast_result.get("error") or "").lower()
                def _manual_fork_response() -> Dict[str, Any]:
                    fork_url = f"https://github.com/{src_owner}/{src_repo}/fork"
                    return {
                        "status": "partial_success",
                        "agent": "devin",
                        "action": "manual_fork_required",
                        "message": "GitHub API rate limit or access restriction encountered while importing. Please fork the template manually, then click Continue to resume.",
                        "fork_url": fork_url,
                        "suggested_owner": target_owner,
                        "suggested_repo": desired_repo_name,
                        "source_repo": f"{src_owner}/{src_repo}"
                    }
                # Immediate fallback on first rate-limit/forbidden to avoid long backoffs
                if ("403" in fr_err) or ("rate limit" in fr_err) or ("forbidden" in fr_err):
                    if progress_job:
                        await broker.publish(progress_job, "done", {"status": "partial_success"})
                    return _manual_fork_response()
                # Fallback to deprecated Importer, then contents-copy
                import_resp = await client.put(
                    f"https://api.github.com/repos/{target_owner}/{desired_repo_name}/import",
                    headers={
                        "Authorization": f"token {write_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        json={
                            "vcs": "git",
                            "vcs_url": f"https://github.com/{src_owner}/{src_repo}.git",
                        },
                        timeout=30.0,
                    )
                if import_resp.status_code == 401 and "Bad credentials" in import_resp.text:
                    import_resp = await client.put(
                        f"https://api.github.com/repos/{target_owner}/{desired_repo_name}/import",
                        headers={
                            "Authorization": f"Bearer {write_token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        json={
                            "vcs": "git",
                            "vcs_url": f"https://github.com/{src_owner}/{src_repo}.git",
                        },
                        timeout=30.0,
                    )
                if import_resp.status_code in (201, 202):
                    if progress_job:
                        await broker.publish(progress_job, "import-ok", {"owner": target_owner, "repo": desired_repo_name})
                    final_repo_name = desired_repo_name
                elif import_resp.status_code == 404 and "deprecated" in import_resp.text.lower():
                    # Fallback: Copy via contents API
                    def copy_progress(payload: dict):
                        if payload.get("event") == "copy-progress" and progress_job:
                            asyncio.create_task(broker.publish(progress_job, "copy-progress", {"copied": payload.get("copied"), "total": payload.get("total")}))
                    def should_cancel_copy():
                        from ..progress import broker as _b
                        return _b.is_cancelled(progress_job) if progress_job else False
                    copy_result = gh_service.copy_into_existing_repo(
                        src_owner,
                        src_repo,
                        f"{target_owner}/{desired_repo_name}",
                        progress_cb=copy_progress,
                        should_cancel=should_cancel_copy,
                    )
                    if not copy_result.get("success"):
                        raise HTTPException(status_code=500, detail=f"Failed to copy repository contents: {copy_result.get('error')}")
                    if progress_job:
                        await broker.publish(progress_job, "copy-ok", {"owner": target_owner, "repo": desired_repo_name})
                    final_repo_name = desired_repo_name
                else:
                    # If we hit a rate limit or forbidden error here, suggest manual fork
                    if import_resp.status_code in (403, 429) or "rate limit" in import_resp.text.lower() or "forbidden" in import_resp.text.lower() or (fr_err and ("403" in fr_err or "rate limit" in fr_err)):
                        if progress_job:
                            await broker.publish(progress_job, "done", {"status": "partial_success"})
                        return _manual_fork_response()
                    raise HTTPException(status_code=import_resp.status_code, detail=f"Failed to import repository: {import_resp.text}")

            # Give GitHub a moment to make repo/fork available
            await asyncio.sleep(3)

            # Pre-assign validation: ensure repo has content, else clean up and prompt manual fork
            async def _repo_is_empty(_owner: str, _repo: str) -> bool:
                try:
                    async with httpx.AsyncClient() as client:
                        # First try contents endpoint (404 indicates empty repo most of the time)
                        cont = await client.get(
                            f"https://api.github.com/repos/{_owner}/{_repo}/contents",
                            headers={"Authorization": f"token {write_token}", "Accept": "application/vnd.github+json"},
                            timeout=20.0,
                        )
                        if cont.status_code == 401 and "Bad credentials" in cont.text:
                            cont = await client.get(
                                f"https://api.github.com/repos/{_owner}/{_repo}/contents",
                                headers={"Authorization": f"Bearer {write_token}", "Accept": "application/vnd.github+json"},
                                timeout=20.0,
                            )
                        if cont.status_code == 404:
                            # Likely empty repo or default branch missing
                            return True
                        if cont.status_code == 200:
                            try:
                                js = cont.json()
                                return isinstance(js, list) and len(js) == 0
                            except Exception:
                                return False
                        # Fallback: repo metadata size
                        meta = await client.get(
                            f"https://api.github.com/repos/{_owner}/{_repo}",
                            headers={"Authorization": f"token {write_token}", "Accept": "application/vnd.github+json"},
                            timeout=20.0,
                        )
                        if meta.status_code == 200 and meta.json().get("size", 0) == 0:
                            return True
                except Exception:
                    return False
                return False

            if await _repo_is_empty((request.customization.owner.strip() or user_login), final_repo_name):
                # Attempt cleanup if we created it during this run
                if created_repo:
                    try:
                        async with httpx.AsyncClient() as client:
                            del_resp = await client.delete(
                                f"https://api.github.com/repos/{(request.customization.owner.strip() or user_login)}/{final_repo_name}",
                                headers={"Authorization": f"token {write_token}", "Accept": "application/vnd.github+json"},
                                timeout=20.0,
                            )
                            if del_resp.status_code == 401 and "Bad credentials" in del_resp.text:
                                await client.delete(
                                    f"https://api.github.com/repos/{(request.customization.owner.strip() or user_login)}/{final_repo_name}",
                                    headers={"Authorization": f"Bearer {write_token}", "Accept": "application/vnd.github+json"},
                                    timeout=20.0,
                                )
                        logger.info(f"Deleted empty repository {final_repo_name} (created during this run)")
                    except Exception as e:
                        logger.warning(f"Failed to delete empty repository {final_repo_name}: {e}")
                # Advise manual fork
                fork_url = f"https://github.com/{src_owner}/{src_repo}/fork"
                result = {
                    "status": "partial_success",
                    "agent": "devin",
                    "action": "manual_fork_required",
                    "message": "Detected empty repository after creation/import. The empty repo has been removed. Please fork the template manually, then click Continue to resume.",
                    "fork_url": fork_url,
                    "suggested_owner": (request.customization.owner.strip() or user_login),
                    "suggested_repo": desired_repo_name,
                    "source_repo": f"{src_owner}/{src_repo}"
                }
                if progress_job:
                    await broker.publish(progress_job, "done", {"status": "partial_success"})
                return result

            # Write agents.md using whichever token we're operating with
            if progress_job:
                await broker.publish(progress_job, "write-agents", {"owner": (request.customization.owner.strip() or user_login), "repo": final_repo_name})
            github_service = GitHubService(github_token=write_token)
            agents_content = github_service.generate_agents_md_content(
                content_type=item_type,
                item=item.__dict__ if hasattr(item, '__dict__') else item,
                customization=request.customization.__dict__
            )
            file_result = github_service.create_file(
                repo_name=f"{(request.customization.owner.strip() or user_login)}/{final_repo_name}",
                file_path="agents.md",
                content=agents_content,
                commit_message="Add agents.md with customization details"
            )
            if not file_result.get("success"):
                logger.warning(f"Failed to create agents.md: {file_result.get('error')}")

            fork_repo_url = f"https://github.com/{(request.customization.owner.strip() or user_login)}/{final_repo_name}"
            prompt = f"""
You are Devin. Implement the following customization for the {title} {item_type}.

Customer: {request.customization.company_name}
Industry: {request.customization.industry}
Use Case: {request.customization.use_case}
Brand Theme: {request.customization.brand_theme}
Primary Color: {request.customization.primary_color}

Scenario:
{request.customization.customer_scenario}

Additional Requirements:
{request.customization.additional_requirements}

Repository to work in (forked from template):
{fork_repo_url}

Tasks:
- Review repository and agents.md for context.
- Apply customizations and open a pull request.
- Document changes in the PR description.
""".strip()

            # Validate prompt length (Devin API has a 30,000 character limit)
            logger.info(f"[agent_service] Prompt length: {len(prompt)} characters")
            if len(prompt) > 29000:  # Leave buffer for safety
                logger.warning(f"[agent_service] Prompt is too long ({len(prompt)} chars), truncating to fit Devin API limit...")
                prompt = prompt[:28000] + "...\n\n[Content truncated due to Devin API length limits]"
                logger.info(f"[agent_service] Truncated prompt length: {len(prompt)} characters")

            devin_payload = {"prompt": prompt, "idempotent": True}
            headers = {"Authorization": f"Bearer {request.api_key}", "Content-Type": "application/json"}

            logger.info(f"[agent_service] === DEVIN API CALL ===")
            logger.info(f"[agent_service] API URL: {settings.DEVIN_API_BASE_URL}/v1/sessions")
            logger.info(f"[agent_service] Headers: {headers}")
            logger.info(f"[agent_service] Payload: {devin_payload}")
            logger.info(f"[agent_service] API Key length: {len(request.api_key) if request.api_key else 0}")

            async with httpx.AsyncClient() as client:
                devin_api_url = settings.DEVIN_API_BASE_URL
                try:
                    if progress_job:
                        await broker.publish(progress_job, "agent-start", {"agent": "devin"})
                    response = await client.post(
                        f"{devin_api_url}/v1/sessions",
                        json=devin_payload,
                        headers=headers,
                        timeout=30.0,
                    )
                    
                    logger.info(f"[agent_service] Response status: {response.status_code}")
                    logger.info(f"[agent_service] Response headers: {dict(response.headers)}")
                    
                    try:
                        response_text = response.text
                        logger.info(f"[agent_service] Response body: {response_text}")
                    except Exception as e:
                        logger.error(f"[agent_service] Failed to read response body: {e}")
                    
                    if response.status_code == 200:
                        devin_response = response.json()
                        
                        result = {
                            "status": "success",
                            "agent": "devin",
                            "session_id": devin_response.get("session_id"),
                            "session_url": devin_response.get("url"),  # API returns "url" not "session_url"
                            "session_status": devin_response.get("status", "created"),
                            "repository_url": fork_repo_url,
                            "message": "Forked template, created agents.md, and started Devin session"
                        }
                        
                        try:
                            async with httpx.AsyncClient() as client:
                                user_resp = await client.get(
                                    "https://api.github.com/user",
                                    headers={"Authorization": f"token {gh_token}"}
                                )
                                if user_resp.status_code == 200:
                                    user_data = user_resp.json()
                                    await self.cosmos_service.store_agent_assignment(
                                        user_id=str(user_data["id"]),
                                        user_login=user_data["login"],
                                        template_id=template_id,
                                        template_title=getattr(item, 'title', item.get('title', 'Unknown Template') if isinstance(item, dict) else 'Unknown Template'),
                                        agent_id="devin",
                                        customization=request.customization.model_dump(),
                                        assignment_response=result
                                    )
                                else:
                                    logger.warning(f"Failed to get user info for assignment storage: {user_resp.status_code}")
                        except Exception as e:
                            logger.error(f"Failed to store Devin assignment: {e}")
                        
                        if progress_job:
                            await broker.publish(progress_job, "done", result)
                        return result
                    elif response.status_code == 401:
                        raise HTTPException(status_code=401, detail="Invalid Devin API key. Please check your credentials.")
                    elif response.status_code == 429:
                        raise HTTPException(status_code=429, detail="Devin API rate limit exceeded. Please try again later.")
                    else:
                        error_detail = f"Devin API error: {response.status_code}"
                        try:
                            error_response = response.json()
                            error_detail += f" - {error_response}"
                            logger.error(f"Devin API error: {response.status_code} - {error_response}")
                        except:
                            error_detail += f" - {response.text}"
                            logger.error(f"Devin API error: {response.status_code} - {response.text}")
                        raise HTTPException(status_code=500, detail=error_detail)
                        
                except httpx.TimeoutException:
                    raise HTTPException(status_code=504, detail="Devin API request timed out. Please try again.")
                except Exception as e:
                    logger.error(f"Devin API request failed: {e}")
                    raise HTTPException(status_code=500, detail=f"Failed to communicate with Devin API: {str(e)}")
        
        elif request.agent_id == "github-copilot":
            return await self._handle_github_copilot_assignment(template_id, request, templates_data, patterns_data, authorization)
        
        elif request.agent_id == "codex-cli":
            return await self._handle_codex_cli_assignment(template_id, request, templates_data, patterns_data, specs_data)
        
        elif request.agent_id == "replit":
            return {
                "status": "success",
                "agent": "replit",
                "message": "Task assigned to Replit Agent (placeholder implementation)"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown agent: {request.agent_id}")

    async def resume_on_existing_repo(self, template_id: str, request: SWEAgentRequest,
                                      templates_data: List, patterns_data: List, specs_data: List,
                                      authorization: Optional[str] = None,
                                      progress_job: Optional[str] = None) -> Dict[str, Any]:
        """
        Resume flow assuming the target repository already exists (manual fork path):
        - Validate repo exists.
        - Write agents.md.
        - Start Devin session.
        - Store assignment in Cosmos.
        """
        item = next((t for t in templates_data if t.id == template_id), None)
        item_type = "template"
        if not item:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
            item = pattern
            item_type = "pattern"

        # Determine GitHub token
        gh_token: Optional[str] = None
        if authorization and authorization.startswith("Bearer "):
            candidate = authorization.split(" ")[1]
            if any(candidate.startswith(p) for p in ("gho_", "ghu_", "ghs_", "ghp_", "github_pat_")):
                gh_token = candidate
        if not gh_token and request.github_token:
            gh_token = request.github_token
        if not gh_token:
            raise HTTPException(status_code=401, detail="GitHub authentication required (missing or invalid token)")

        # Identify user (for storage defaults)
        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {gh_token}"}
            )
            if user_resp.status_code != 200:
                raise HTTPException(status_code=user_resp.status_code, detail="Failed to identify GitHub user")
            user_data = user_resp.json()
            user_login = user_data.get("login")

        owner = (request.customization.owner or user_login).strip()
        repo = (request.customization.repo or "").strip()
        if not repo:
            # Fallback: derive from template title and company
            title = getattr(item, 'title', item.get('title', 'template') if isinstance(item, dict) else 'template')
            import re as _re
            safe_name = _re.sub(r'[^a-zA-Z0-9-]', '-', title.lower())
            company = request.customization.company_name or "customer"
            company_safe = _re.sub(r'[^a-zA-Z0-9-]', '-', company.lower()).strip('-') or 'customer'
            repo = f"{safe_name}-{company_safe}"

        # Validate repo exists
        async with httpx.AsyncClient() as client:
            get_repo_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"},
                timeout=20.0,
            )
            if get_repo_resp.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found. Please fork first and try again.")

        # Ensure repo is not empty
        async with httpx.AsyncClient() as client:
            contents_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents",
                headers={"Authorization": f"token {gh_token}", "Accept": "application/vnd.github+json"},
                timeout=20.0,
            )
            if contents_resp.status_code == 404:
                raise HTTPException(status_code=400, detail="The repository is empty. Please fork the template (with contents) and try Continue again.")

        # Progress event
        if progress_job:
            await broker.publish(progress_job, "write-agents", {"owner": owner, "repo": repo})

        # Write agents.md
        github_service = GitHubService(github_token=gh_token)
        agents_content = github_service.generate_agents_md_content(
            content_type=item_type,
            item=item.__dict__ if hasattr(item, '__dict__') else item,
            customization=request.customization.__dict__
        )
        file_result = github_service.create_file(
            repo_name=f"{owner}/{repo}",
            file_path="agents.md",
            content=agents_content,
            commit_message="Add agents.md with customization details"
        )
        if not file_result.get("success"):
            logger.warning(f"Failed to create agents.md during resume: {file_result.get('error')}")

        # Start Devin session
        prompt_title = getattr(item, 'title', item.get('title', 'template') if isinstance(item, dict) else 'template')
        fork_repo_url = f"https://github.com/{owner}/{repo}"
        prompt = f"""
You are Devin. Implement the following customization for the {prompt_title} {item_type}.

Customer: {request.customization.company_name}
Industry: {request.customization.industry}
Use Case: {request.customization.use_case}
Brand Theme: {request.customization.brand_theme}
Primary Color: {request.customization.primary_color}

Scenario:
{request.customization.customer_scenario}

Additional Requirements:
{request.customization.additional_requirements}

Repository to work in (forked from template):
{fork_repo_url}

Tasks:
- Review repository and agents.md for context.
- Apply customizations and open a pull request.
- Document changes in the PR description.
""".strip()

        devin_payload = {"prompt": prompt, "idempotent": True}
        headers = {"Authorization": f"Bearer {request.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            devin_api_url = settings.DEVIN_API_BASE_URL
            if progress_job:
                await broker.publish(progress_job, "agent-start", {"agent": "devin"})
            response = await client.post(
                f"{devin_api_url}/v1/sessions",
                json=devin_payload,
                headers=headers,
                timeout=30.0,
            )
            if response.status_code != 200:
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid Devin API key. Please check your credentials.")
                if response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Devin API rate limit exceeded. Please try again later.")
                logger.error(f"Devin API error on resume: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail=f"Devin API error: {response.status_code}")

            devin_response = response.json()
            result = {
                "status": "success",
                "agent": "devin",
                "session_id": devin_response.get("session_id"),
                "session_url": devin_response.get("session_url"),
                "session_status": devin_response.get("status", "created"),
                "repository_url": fork_repo_url,
                "message": "Resumed: created agents.md and started Devin session"
            }

        # Store assignment
        try:
            await self.cosmos_service.store_agent_assignment(
                user_id=str(user_data["id"]),
                user_login=user_login,
                template_id=template_id,
                template_title=getattr(item, 'title', item.get('title', 'Unknown Template') if isinstance(item, dict) else 'Unknown Template'),
                agent_id="devin",
                customization=request.customization.model_dump(),
                assignment_response=result
            )
        except Exception as e:
            logger.error(f"Failed to store resumed Devin assignment: {e}")

        if progress_job:
            await broker.publish(progress_job, "done", result)
        return result
    
    async def _handle_github_copilot_assignment(self, template_id: str, request: SWEAgentRequest,
                                              templates_data: List, patterns_data: List,
                                              authorization: Optional[str]) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": "github-copilot",
            "message": "GitHub Copilot assignment implementation needed"
        }
    
    async def _handle_codex_cli_assignment(self, template_id: str, request: SWEAgentRequest,
                                         templates_data: List, patterns_data: List, specs_data: List) -> Dict[str, Any]:
        return {
            "status": "success",
            "agent": "codex-cli",
            "message": "Codex CLI assignment implementation needed"
        }
    
    async def get_user_assignments(self, user_id: str) -> List[Dict[str, Any]]:
        assignments = await self.cosmos_service.get_user_assignments(user_id)
        return [assignment.model_dump() for assignment in assignments]
    
    async def get_assignment_details(self, assignment_id: str, user_id: str) -> Dict[str, Any]:
        assignments = await self.cosmos_service.get_user_assignments(user_id)
        assignment = next((a for a in assignments if a.id == assignment_id), None)
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        return assignment.model_dump()
