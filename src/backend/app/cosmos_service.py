import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError

logger = logging.getLogger(__name__)

class AgentAssignment(BaseModel):
    id: str
    user_id: str
    user_login: str
    template_id: str
    template_title: str
    agent_id: str
    status: str
    session_status: Optional[str] = None
    repository_url: Optional[str] = None
    session_url: Optional[str] = None
    session_id: Optional[str] = None
    issue_url: Optional[str] = None
    issue_number: Optional[int] = None
    customization: Dict[str, Any]
    context_markdown: str
    created_at: str
    updated_at: str

class UserSession(BaseModel):
    id: str
    user_id: str
    user_login: str
    assignments: List[str]
    created_at: str
    updated_at: str

class CosmosService:
    def __init__(self):
        self.connection_string = os.getenv("COSMOS_CONNECTION_STRING")
        if not self.connection_string:
            logger.warning("COSMOS_CONNECTION_STRING not found, running in mock mode")
            self.mock_mode = True
            return
        
        self.mock_mode = False
        self.client = CosmosClient.from_connection_string(self.connection_string)
        self.database_name = os.getenv("COSMOS_DATABASE_ID", "aifoundry")
        self.assignments_container_name = "agent_assignments"
        self.sessions_container_name = "user_sessions"
        
        self._ensure_database_and_containers()
    
    def _ensure_database_and_containers(self):
        try:
            database = self.client.create_database_if_not_exists(id=self.database_name)
            
            database.create_container_if_not_exists(
                id=self.assignments_container_name,
                partition_key=PartitionKey(path="/user_id")
            )
            
            database.create_container_if_not_exists(
                id=self.sessions_container_name,
                partition_key=PartitionKey(path="/user_id")
            )
            
            logger.info("Cosmos DB database and containers initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            raise
    
    async def store_agent_assignment(
        self,
        user_id: str,
        user_login: str,
        template_id: str,
        template_title: str,
        agent_id: str,
        customization: Dict[str, Any],
        assignment_response: Dict[str, Any]
    ) -> str:
        if self.mock_mode:
            logger.info(f"Mock mode: Would store assignment for user {user_login}")
            return "mock-assignment-id"
        
        assignment_id = f"{user_id}_{template_id}_{agent_id}_{int(datetime.now().timestamp())}"
        
        context_markdown = self._generate_context_markdown(
            template_title, agent_id, customization, assignment_response
        )
        
        assignment = AgentAssignment(
            id=assignment_id,
            user_id=user_id,
            user_login=user_login,
            template_id=template_id,
            template_title=template_title,
            agent_id=agent_id,
            status=assignment_response.get("status", "unknown"),
            session_status=assignment_response.get("session_status"),
            repository_url=assignment_response.get("repository_url"),
            session_url=assignment_response.get("session_url"),
            session_id=assignment_response.get("session_id"),
            issue_url=assignment_response.get("issue_url"),
            issue_number=assignment_response.get("issue_number"),
            customization=customization,
            context_markdown=context_markdown,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        try:
            database = self.client.get_database_client(self.database_name)
            container = database.get_container_client(self.assignments_container_name)
            container.create_item(body=assignment.model_dump())
            
            await self._update_user_session(user_id, user_login, assignment_id)
            
            logger.info(f"Stored assignment {assignment_id} for user {user_login}")
            return assignment_id
        except Exception as e:
            logger.error(f"Failed to store assignment: {e}")
            raise
    
    def _generate_context_markdown(
        self,
        template_title: str,
        agent_id: str,
        customization: Dict[str, Any],
        assignment_response: Dict[str, Any]
    ) -> str:
        markdown = f"""# {template_title} - {agent_id.title()} Assignment

- **Agent**: {agent_id}
- **Status**: {assignment_response.get('status', 'unknown')}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

- **Company**: {customization.get('company_name', 'Not specified')}
- **Industry**: {customization.get('industry', 'Not specified')}
- **Use Case**: {customization.get('use_case', 'Not specified')}
- **Primary Color**: {customization.get('primary_color', 'Not specified')}

{customization.get('customer_scenario', 'Not provided')}

{customization.get('brand_theme', 'Not provided')}

{customization.get('additional_requirements', 'None')}

- **Use MCP Tools**: {customization.get('use_mcp_tools', False)}
- **Use A2A Communication**: {customization.get('use_a2a', False)}

"""
        
        if assignment_response.get('repository_url'):
            markdown += f"- **Repository**: [{assignment_response['repository_url']}]({assignment_response['repository_url']})\n"
        
        if assignment_response.get('session_url'):
            markdown += f"- **Session**: [{assignment_response['session_url']}]({assignment_response['session_url']})\n"
        
        if assignment_response.get('issue_url'):
            markdown += f"- **Issue**: [{assignment_response['issue_url']}]({assignment_response['issue_url']})\n"
        
        if assignment_response.get('message'):
            markdown += f"\n### Message\n{assignment_response['message']}\n"
        
        return markdown
    
    async def _update_user_session(self, user_id: str, user_login: str, assignment_id: str):
        if self.mock_mode:
            return
        
        try:
            database = self.client.get_database_client(self.database_name)
            container = database.get_container_client(self.sessions_container_name)
            
            try:
                session_data = container.read_item(item=user_id, partition_key=user_id)
                session = UserSession(**session_data)
                session.assignments.append(assignment_id)
                session.updated_at = datetime.now().isoformat()
            except CosmosResourceNotFoundError:
                session = UserSession(
                    id=user_id,
                    user_id=user_id,
                    user_login=user_login,
                    assignments=[assignment_id],
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
            
            container.upsert_item(body=session.model_dump())
        except Exception as e:
            logger.error(f"Failed to update user session: {e}")
    
    async def get_user_assignments(self, user_id: str) -> List[AgentAssignment]:
        if self.mock_mode:
            return []
        
        try:
            database = self.client.get_database_client(self.database_name)
            container = database.get_container_client(self.assignments_container_name)
            
            query = "SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@user_id", "value": user_id}],
                partition_key=user_id
            ))
            
            return [AgentAssignment(**item) for item in items]
        except Exception as e:
            logger.error(f"Failed to get user assignments: {e}")
            return []
