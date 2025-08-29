from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
CATALOG = ROOT / "catalog.json"
FEATURED = ROOT / "featured.json"

BASE = "https://azure.github.io"
HOME = f"{BASE}/ai-app-templates/"

LANGS = {".NET/C#", "JavaScript", "TypeScript", "Python", "Java", "Go"}
TASKS = {"Agent", "Interactive Chat", "Guided Search", "Completions", "LLM Ops"}


def slugify(text: str) -> str:
    return (
        "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
        .strip("-")
        .replace("--", "-")
    )


def normalize(obj: dict) -> dict:
    obj.setdefault("tags", [])
    obj.setdefault("languages", [])
    obj.setdefault("models", [])
    obj.setdefault("databases", [])
    obj.setdefault("collection", "Azure AI App Templates")
    obj.setdefault("task", "Agent")
    obj.setdefault("pattern", None)
    obj.setdefault("fork_count", 0)
    obj.setdefault("star_count", 0)
    obj.setdefault("is_featured", False)
    obj.setdefault("icon", "🤖")
    obj.setdefault("created_at", date.today().isoformat())
    return obj

def infer_task_from_text(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["multi agent", "agent", "automation", "orchestrator", "function calling"]):
        return "Agent"
    if any(k in t for k in ["chat", "assistant", "copilot chat", "conversational"]):
        return "Interactive Chat"
    if any(k in t for k in ["search", "rag", "retrieval", "knowledge mining"]):
        return "Guided Search"
    if any(k in t for k in ["completion", "summar", "generation", "prompt", "text generation"]):
        return "Completions"
    if any(k in t for k in ["observability", "eval", "monitor", "ops", "guardrail"]):
        return "LLM Ops"
    return "Agent"


def parse_detail_page(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "lxml")

    title_el = soup.select_one("h1, header h1, .post-title")
    title = (
        title_el.get_text(strip=True)
        if title_el
        else url.rstrip("/").split("/")[-1].replace("-", " ").title()
    )
    desc_el = soup.select_one("meta[name='description']") or soup.select_one("p")
    description = (
        desc_el.get("content", "")
        if desc_el and desc_el.name == "meta"
        else (desc_el.get_text(strip=True) if desc_el else "")
    )

    gh_a = soup.select_one('a[href*="github.com"]')
    github_url = gh_a["href"].strip() if gh_a else ""

    chips = [c.get_text(strip=True) for c in soup.select(".chip, .tag, .Label, .badge")]
    languages = [c for c in chips if c in LANGS]
    task = next((c for c in chips if c in TASKS), "Agent")
    models = [c for c in chips if any(k in c for k in ["GPT", "Phi", "Llama", "Mistral"])]
    databases = [
        c
        for c in chips
        if any(x in c for x in ["Cosmos", "Search", "PostgreSQL", "Pinecone", "Redis", "SQL", "Storage"])
    ]

    if not github_url and "/repo/" in url:
        slug = urlparse(url).path.split("/repo/")[-1].strip("/")
        if slug and "/" in slug:
            github_url = f"https://github.com/{slug}"

    if not github_url:
        return None

    obj = {
        "id": slugify(urlparse(github_url).path.rstrip("/").split("/")[-1]),
        "title": title,
        "description": description,
        "tags": chips,
        "languages": languages,
        "models": models,
        "databases": databases,
        "collection": "Azure AI App Templates",
        "task": task,
        "pattern": None,
        "github_url": github_url,
        "fork_count": 0,
        "star_count": 0,
        "is_featured": False,
        "icon": "🤖" if task == "Agent" else "💬",
        "created_at": date.today().isoformat(),
    }
    obj = enrich_from_github(obj)
    return obj

def enrich_from_github(obj: dict) -> dict:
    url = obj.get("github_url") or ""
    try:
        parts = urlparse(url).path.strip("/").split("/")
        if len(parts) < 2:
            return obj
        owner, repo = parts[0], parts[1]
        headers = {
            "User-Agent": "aifoundry-sync/gh",
            "Accept": "application/vnd.github+json",
        }
        with httpx.Client(timeout=25, headers=headers) as c:
            r = c.get(f"https://api.github.com/repos/{owner}/{repo}")
            data = {}
            if r.status_code != 403:
                r.raise_for_status()
                data = r.json()
            desc = (data.get("description") or "").strip() if isinstance(data, dict) else ""
            if desc:
                obj["description"] = desc
            if isinstance(data, dict):
                obj["star_count"] = int(data.get("stargazers_count") or 0)
                obj["fork_count"] = int(data.get("forks_count") or 0)
                main_lang = data.get("language")
                if main_lang and main_lang not in obj.get("languages", []):
                    obj["languages"] = list({*obj.get("languages", []), main_lang})
                topics = data.get("topics") or []
                if topics:
                    obj["tags"] = list({*obj.get("tags", []), *topics})
            task_source = " ".join([obj.get("title",""), obj.get("description","") or desc, url, " ".join(data.get("topics", []) if isinstance(data, dict) else [])])
            obj["task"] = infer_task_from_text(task_source)

            if not (obj.get("description") or "").strip():
                gh_html = f"https://github.com/{owner}/{repo}"
                hr = c.get(gh_html, headers={"User-Agent": "aifoundry-sync/html"})
                if hr.status_code == 200:
                    soup = BeautifulSoup(hr.text, "lxml")
                    meta = soup.select_one('meta[property="og:description"]') or soup.select_one('meta[name="description"]')
                    if meta:
                        mdesc = (meta.get("content") or "").strip()
                        if mdesc:
                            obj["description"] = mdesc
                            obj["task"] = infer_task_from_text(" ".join([obj.get("title",""), mdesc]))

            if not (obj.get("description") or "").strip():
                rr = c.get(f"https://api.github.com/repos/{owner}/{repo}/readme")
                if rr.status_code == 200:
                    rd = rr.json()
                    import base64
                    content = base64.b64decode((rd.get("content") or "").encode()).decode(errors="ignore")
                    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
                    lines = [ln for ln in lines if not ln.startswith("#") and "badge" not in ln.lower()]
                    if lines:
                        blurb = lines[0]
                        for ln in lines[1:5]:
                            if len(blurb) < 60 and len(ln) > len(blurb):
                                blurb = ln
                        obj["description"] = (blurb[:200] + ("…" if len(blurb) > 200 else ""))
                        obj["task"] = infer_task_from_text(" ".join([obj.get("title",""), blurb]))
    except Exception:
        pass
    return obj

    return obj


def discover_detail_routes(client: httpx.Client) -> list[str]:
    site_map = f"{HOME}sitemap.xml"
    r = client.get(site_map)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "xml")
    routes: list[str] = []
    for loc in soup.select("loc"):
        u = loc.get_text(strip=True)
        if "/ai-app-templates/repo/" in u:
            routes.append(u)
    return sorted(set(routes))


def fetch():
    with httpx.Client(timeout=45, headers={"User-Agent": "aifoundry-sync/1.2"}) as client:
        detail_links = discover_detail_routes(client)
        print(f"discover_detail_routes -> {len(detail_links)}")

        items = []
        for u in detail_links:
            obj = None
            try:
                r = client.get(u)
                r.raise_for_status()
                obj = parse_detail_page(r.text, u)
            except Exception:
                obj = None
            if not obj:
                slug = urlparse(u).path.split("/repo/")[-1].strip("/")
                if slug and "/" in slug:
                    owner, repo = slug.split("/", 1)
                    gh = f"https://github.com/{owner}/{repo}"
                    obj = normalize({
                        "id": slugify(repo),
                        "title": repo.replace("-", " ").title(),
                        "description": "",
                        "tags": [],
                        "languages": [],
                        "models": [],
                        "databases": [],
                        "collection": "Azure AI App Templates",
                        "task": infer_task_from_text(repo),
                        "pattern": None,
                        "github_url": gh,
                        "fork_count": 0,
                        "star_count": 0,
                        "is_featured": False,
                        "icon": "🤖",
                    })
                    obj = enrich_from_github(obj)
            if obj:
                items.append(obj)
        print(f"built_items -> {len(items)}")

    seen = set()
    deduped = []
    for obj in items:
        key = obj.get("github_url") or obj.get("title")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(obj)
    print(f"deduped -> {len(deduped)}")

    try:
        featured_urls = set(json.loads(FEATURED.read_text()))
    except Exception:
        featured_urls = set()
    for o in deduped:
        if o["github_url"] in featured_urls:
            o["is_featured"] = True

    existing_urls = {o.get("github_url") for o in deduped}
    for f_url in featured_urls:
        if f_url not in existing_urls:
            path = urlparse(f_url).path.strip("/")
            parts = path.split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                o = normalize({
                    "id": slugify(repo),
                    "title": repo.replace("-", " ").title(),
                    "description": "",
                    "tags": [],
                    "languages": [],
                    "models": [],
                    "databases": [],
                    "collection": "Azure AI App Templates",
                    "task": infer_task_from_text(repo),
                    "pattern": None,
                    "github_url": f_url,
                    "fork_count": 0,
                    "star_count": 0,
                    "is_featured": True,
                    "icon": "🤖",
                })
                o = enrich_from_github(o)
                deduped.append(o)

    CATALOG.write_text(json.dumps(deduped, indent=2), encoding="utf-8")
    return deduped


if __name__ == "__main__":
    data = fetch()
    print(f"Wrote {len(data)} templates to {CATALOG}")
