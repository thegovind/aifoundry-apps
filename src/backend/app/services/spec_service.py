from typing import List, Optional, Dict
from pathlib import Path
import json
import logging
import uuid
from datetime import datetime
from ..models.schemas import Spec, SpecCreateRequest

logger = logging.getLogger(__name__)

class SpecService:
    def __init__(self):
        self.specs_path = Path(__file__).parent.parent / "specs.json"
        self._specs_data: List[Spec] = []
        self._spec_by_id: Dict[str, Spec] = {}
        self._load_specs()
    
    def _load_specs(self) -> None:
        specs: List[Spec] = []
        if self.specs_path.exists():
            try:
                with self.specs_path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                for obj in raw:
                    try:
                        specs.append(Spec(**obj))
                    except Exception as e:
                        logger.warning(f"Skipping invalid spec: {e}")
            except Exception as e:
                logger.error(f"Error loading specs: {e}")
        
        self._specs_data = specs
        self._spec_by_id = {s.id: s for s in specs}
    
    def _save_specs(self) -> None:
        with self.specs_path.open("w", encoding="utf-8") as f:
            json.dump([spec.model_dump() for spec in self._specs_data], f, indent=2)
    
    def get_all_specs(self) -> List[Spec]:
        return self._specs_data
    
    def get_spec_by_id(self, spec_id: str) -> Optional[Spec]:
        return self._spec_by_id.get(spec_id)
    
    def create_spec(self, request: SpecCreateRequest) -> Spec:
        new_spec = Spec(
            id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            content=request.content,
            tags=request.tags,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            phase="specification",
            specification=request.content,  # Initial content goes to specification
            plan=None,
            tasks=None,
            branch_name=None,
            feature_number=None
        )
        
        self._specs_data.append(new_spec)
        self._spec_by_id[new_spec.id] = new_spec
        self._save_specs()
        
        return new_spec
    
    def update_spec(self, spec_id: str, request: SpecCreateRequest) -> Optional[Spec]:
        spec = self._spec_by_id.get(spec_id)
        if not spec:
            return None
        
        updated_spec = Spec(
            id=spec.id,
            title=request.title,
            description=request.description,
            content=request.content,
            tags=request.tags,
            created_at=spec.created_at,
            updated_at=datetime.now().isoformat(),
            phase=spec.phase,
            specification=spec.specification,
            plan=spec.plan,
            tasks=spec.tasks,
            branch_name=spec.branch_name,
            feature_number=spec.feature_number
        )
        
        for i, s in enumerate(self._specs_data):
            if s.id == spec_id:
                self._specs_data[i] = updated_spec
                break
        
        self._spec_by_id[spec_id] = updated_spec
        self._save_specs()
        
        return updated_spec
    
    def update_spec_phase(self, spec_id: str, phase: str, **kwargs) -> Optional[Spec]:
        """Update a specific phase of the spec"""
        spec = self._spec_by_id.get(spec_id)
        if not spec:
            return None
        
        updated_spec = Spec(
            id=spec.id,
            title=spec.title,
            description=spec.description,
            content=spec.content,
            tags=spec.tags,
            created_at=spec.created_at,
            updated_at=datetime.now().isoformat(),
            phase=phase,
            specification=kwargs.get('specification', spec.specification),
            plan=kwargs.get('plan', spec.plan),
            tasks=kwargs.get('tasks', spec.tasks),
            branch_name=kwargs.get('branch_name', spec.branch_name),
            feature_number=kwargs.get('feature_number', spec.feature_number)
        )
        
        for i, s in enumerate(self._specs_data):
            if s.id == spec_id:
                self._specs_data[i] = updated_spec
                break
        
        self._spec_by_id[spec_id] = updated_spec
        self._save_specs()
        
        return updated_spec
