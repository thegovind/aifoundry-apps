from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from ...models.schemas import Template, FilterOptions, CustomizationRequest, TaskBreakdownResponse
from ...services.template_service import TemplateService
from ...api.dependencies import get_template_service
from ...data.static_data import patterns_data

router = APIRouter()

@router.get("", response_model=List[Template])
async def get_templates(
    search: Optional[str] = Query(None, description="Search templates by title or description"),
    task: Optional[str] = Query(None, description="Filter by task type"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    collection: Optional[str] = Query(None, description="Filter by collection"),
    model: Optional[str] = Query(None, description="Filter by AI model"),
    database: Optional[str] = Query(None, description="Filter by database"),
    sort: Optional[str] = Query("Most Popular", description="Sort order"),
    template_service: TemplateService = Depends(get_template_service)
):
    filtered = template_service.filter_templates(search, task, language, collection, model, database, sort)
    return [t.model_dump() for t in filtered]

@router.get("/featured", response_model=List[Template])
async def get_featured_templates(template_service: TemplateService = Depends(get_template_service)):
    featured = template_service.get_featured_templates()
    return [t.model_dump() for t in featured]

@router.get("/{template_id}", response_model=Template)
async def get_template(template_id: str, template_service: TemplateService = Depends(get_template_service)):
    t = template_service.get_template_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t.model_dump()

@router.post("/{template_id}/breakdown")
async def generate_task_breakdown(template_id: str, request: CustomizationRequest):
    """Generate task breakdown using Azure OpenAI"""
    from ...core.config import settings
    from openai import AzureOpenAI
    
    try:
        template_service = get_template_service()
        template = template_service.get_template_by_id(template_id)
        pattern = None
        
        if not template:
            pattern = next((p for p in patterns_data if p["id"] == template_id), None)
            if not pattern:
                raise HTTPException(status_code=404, detail="Template or pattern not found")
        
        try:
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            if template:
                system_prompt = f"""You are an AI assistant that helps break down template customization tasks into actionable steps.

Template: {template.title}
Description: {template.description}
Task Type: {template.task}
Languages: {', '.join(template.languages)}
Models: {', '.join(template.models)}
"""
            else:
                pattern_title = pattern.get("title", "Unknown Pattern")
                pattern_type = pattern.get("type", "Unknown Type")
                system_prompt = f"""You are an AI assistant that helps break down multi-agent pattern implementation tasks into actionable steps.

Pattern: {pattern_title}
Type: {pattern_type}
Description: {pattern.get("description", "No description available")}
"""

            user_prompt = f"""Break down the customization task into 5 specific, actionable tasks for the following requirements:

Company: {request.company_name}
Industry: {request.industry}
Use Case: {request.use_case}
Customer Scenario: {request.customer_scenario}
Brand Theme: {request.brand_theme}
Primary Color: {request.primary_color}
Additional Requirements: {request.additional_requirements}

Return exactly 5 tasks in JSON format with this structure:
[
  {{
    "id": "task-1",
    "title": "Task title",
    "description": "Detailed description",
    "estimatedTime": "X-Y hours",
    "estimatedTokens": "X-Y tokens",
    "priority": "high/medium/low",
    "status": "pending"
  }}
]"""

            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            import json
            tasks_json = response.choices[0].message.content.strip()
            
            if tasks_json.startswith("```json"):
                tasks_json = tasks_json[7:-3].strip()
            elif tasks_json.startswith("```"):
                tasks_json = tasks_json[3:-3].strip()
            
            try:
                tasks = json.loads(tasks_json)
                return {"tasks": tasks}
            except json.JSONDecodeError:
                if template:
                    template_title = template.title
                else:
                    template_title = pattern.get("title", "Unknown Pattern")
                    pattern_type = pattern.get("type", "Unknown Type")
                
                return {
                    "tasks": [
                        {
                            "id": "task-1",
                            "title": f"Implement {template_title} for {request.company_name}",
                            "description": f"Design and implement the {template_title} using {request.customer_scenario}. Set up the core pattern structure and agent coordination.",
                            "estimatedTime": "4-6 hours",
                            "estimatedTokens": "18000-28000 tokens",
                            "priority": "high",
                            "status": "pending"
                        },
                        {
                            "id": "task-2", 
                            "title": "Configure agent interactions",
                            "description": f"Set up agent communication and data flow according to {pattern_type if pattern else template.task} pattern. Configure input format: {request.brand_theme.split(' → ')[0] if ' → ' in request.brand_theme else 'Not specified'}.",
                            "estimatedTime": "3-4 hours",
                            "estimatedTokens": "12000-18000 tokens",
                            "priority": "high",
                            "status": "pending"
                        },
                        {
                            "id": "task-3",
                            "title": "Implement output formatting",
                            "description": f"Configure output generation to match required format: {request.brand_theme.split(' → ')[1] if ' → ' in request.brand_theme else 'Not specified'}. Ensure proper data transformation.",
                            "estimatedTime": "2-3 hours", 
                            "estimatedTokens": "8000-12000 tokens",
                            "priority": "medium",
                            "status": "pending"
                        },
                        {
                            "id": "task-4",
                            "title": "Apply agent configuration",
                            "description": f"Implement specific agent settings: {request.additional_requirements}. Fine-tune agent behavior and performance.",
                            "estimatedTime": "2-3 hours",
                            "estimatedTokens": "8000-12000 tokens",
                            "priority": "medium",
                            "status": "pending"
                        },
                        {
                            "id": "task-5",
                            "title": "Testing and validation",
                            "description": f"Test the {template_title} implementation with sample data. Validate pattern behavior and performance for {request.use_case} use case.",
                            "estimatedTime": "2-3 hours",
                            "estimatedTokens": "6000-10000 tokens",
                            "priority": "high",
                            "status": "pending"
                        }
                    ]
                }
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating task breakdown: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating task breakdown: {str(e)}")
