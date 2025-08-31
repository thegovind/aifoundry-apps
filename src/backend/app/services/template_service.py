from typing import List, Optional, Dict
from pathlib import Path
import json
import logging
from ..models.schemas import Template, FilterOptions

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self):
        self.catalog_path = Path(__file__).parent.parent / "catalog.json"
        self.featured_path = Path(__file__).parent.parent / "featured.json"
        self._templates_data: List[Template] = []
        self._template_by_id: Dict[str, Template] = {}
        self._load_catalog()
    
    def _load_catalog(self) -> None:
        items: List[Template] = []
        raw: List[Dict] = []
        
        if self.catalog_path.exists():
            with self.catalog_path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        else:
            logger.warning("catalog.json not found; returning empty catalog")
        
        try:
            with self.featured_path.open("r", encoding="utf-8") as f:
                featured_urls = set(json.load(f))
        except FileNotFoundError:
            featured_urls = set()
        
        for obj in raw:
            try:
                is_featured = obj.get("github_url") in featured_urls or obj.get("is_featured", False)
                obj["is_featured"] = bool(is_featured)
                items.append(Template(**obj))
            except Exception as e:
                logger.warning(f"Skipping invalid template: {e}")
        
        self._templates_data = items
        self._template_by_id = {t.id: t for t in items}
    
    def get_all_templates(self) -> List[Template]:
        return self._templates_data
    
    def get_template_by_id(self, template_id: str) -> Optional[Template]:
        return self._template_by_id.get(template_id)
    
    def get_featured_templates(self) -> List[Template]:
        return [t for t in self._templates_data if t.is_featured]
    
    def filter_templates(self, search: Optional[str] = None, task: Optional[str] = None,
                        language: Optional[str] = None, collection: Optional[str] = None,
                        model: Optional[str] = None, database: Optional[str] = None,
                        sort: Optional[str] = "Most Popular") -> List[Template]:
        filtered = list(self._templates_data)

        if search:
            s = search.lower()
            filtered = [t for t in filtered if s in t.title.lower() or s in t.description.lower()]

        if task:
            filtered = [t for t in filtered if task == t.task or task in t.tags]

        if language:
            filtered = [t for t in filtered if language in t.languages]

        if collection:
            filtered = [t for t in filtered if t.collection == collection]

        if model:
            filtered = [t for t in filtered if model in t.models]

        if database:
            filtered = [t for t in filtered if database in t.databases]

        if sort == "Most Popular":
            filtered.sort(key=lambda t: t.star_count, reverse=True)
        elif sort == "Most Recent":
            filtered.sort(key=lambda t: t.created_at or "", reverse=True)
        elif sort == "Most Forked":
            filtered.sort(key=lambda t: t.fork_count, reverse=True)

        return filtered
    
    def get_filter_options(self) -> FilterOptions:
        tasks = sorted({t.task for t in self._templates_data if t.task})
        languages = sorted({lang for t in self._templates_data for lang in t.languages})
        collections = sorted({t.collection for t in self._templates_data if t.collection})
        models = sorted({m for t in self._templates_data for m in t.models})
        databases = sorted({d for t in self._templates_data for d in t.databases})
        patterns = sorted({t.pattern for t in self._templates_data if t.pattern})
        return FilterOptions(
            tasks=tasks, languages=languages, collections=collections,
            models=models, databases=databases, patterns=patterns
        )
