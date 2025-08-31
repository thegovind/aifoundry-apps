from fastapi import APIRouter, Depends, Header
from typing import Optional, Dict, Any
from ...models.schemas import SWEAgentRequest
from ...services.agent_service import AgentService
from ...services.template_service import TemplateService
from ...api.dependencies import get_agent_service, get_template_service
from ...data.static_data import patterns_data
from ...progress import broker

router = APIRouter()

@router.post("/templates/{template_id}/assign")
async def assign_to_swe_agent(
    template_id: str, 
    request: SWEAgentRequest, 
    authorization: Optional[str] = Header(None),
    x_progress_job: Optional[str] = Header(None),
    agent_service: AgentService = Depends(get_agent_service),
    template_service: TemplateService = Depends(get_template_service)
):
    """Assign customization task to SWE agent"""
    templates_data = template_service.get_all_templates()
    specs_data = []  # TODO: Get from spec service
    # Notify start if client provided a progress job id
    if x_progress_job:
        await broker.publish(x_progress_job, "start", {"template_id": template_id, "agent": request.agent_id})

    return await agent_service.assign_to_swe_agent(
        template_id, request, templates_data, patterns_data, specs_data, authorization, progress_job=x_progress_job
    )

@router.post("/templates/{template_id}/resume")
async def resume_assignment_on_existing_repo(
    template_id: str,
    request: SWEAgentRequest,
    authorization: Optional[str] = Header(None),
    x_progress_job: Optional[str] = Header(None),
    agent_service: AgentService = Depends(get_agent_service),
    template_service: TemplateService = Depends(get_template_service)
):
    """Resume assignment flow assuming the repository already exists (manual fork path)."""
    templates_data = template_service.get_all_templates()
    specs_data = []
    if x_progress_job:
        await broker.publish(x_progress_job, "start", {"template_id": template_id, "agent": request.agent_id, "resume": True})
    return await agent_service.resume_on_existing_repo(
        template_id, request, templates_data, patterns_data, specs_data, authorization, progress_job=x_progress_job
    )

@router.post("/templates/{template_id}/deploy")
async def deploy_template_to_github(template_id: str, request: dict):
    """Deploy template to user's GitHub repository with agent configuration"""
    return {
        "status": "success",
        "message": "Template deployment functionality to be implemented"
    }

@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str, authorization: str = Header(...)):
    """Get Devin session status"""
    return {
        "session_id": session_id,
        "status": "running",
        "message": "Session status functionality to be implemented"
    }
