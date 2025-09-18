import pytest


def test_system_check_partial_status(client):
    resp = client.get("/api/specs/system-check")
    assert resp.status_code == 200
    data = resp.json()
    assert set(["status", "checks", "messages"]).issubset(data.keys())
    assert isinstance(data["checks"], dict)
    # In CI/local without secrets, expect partial readiness
    assert data["status"] in {"partial", "ready"}
    assert isinstance(data["messages"], list)


@pytest.mark.parametrize(
    "agent,expected_file",
    [
        ("claude", ".claude/commands/specify.md"),
        ("gemini", ".gemini/commands/specify.toml"),
        ("copilot", ".github/prompts/specify.prompt.md"),
    ],
)
def test_spec_kit_init_agent_files(client, agent, expected_file):
    body = {"project_name": "demo-project", "ai_agent": agent}
    resp = client.post("/api/specs/spec-kit-init", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert isinstance(data.get("project_structure"), dict)
    agent_files = data["project_structure"].get("agent_files", [])
    assert expected_file in agent_files


def test_constitutional_validation_compliant(client):
    body = {
        "plan": (
            "Use popular framework and existing libraries via npm/pip. "
            "Provide CLI commands with arguments. "
            "Write unit tests, integration tests and contract tests. "
            "Keep a direct, simple approach. "
            "Plan real environment e2e and API tests; avoid mocks."
        ),
        "tech_stack": "fastapi, postgres",
        "architecture": "simple direct approach",
    }
    resp = client.post("/api/specs/constitutional-validation", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_compliant"] is True
    gates = data.get("gates_passed", {})
    # Ensure all expected gates present and passing
    for k in [
        "library_first",
        "cli_interface",
        "test_first",
        "simplicity",
        "anti_abstraction",
        "integration_first",
    ]:
        assert k in gates and gates[k] is True


def test_constitutional_validation_non_compliant(client):
    body = {
        "plan": (
            "Build from scratch with custom implementation. "
            "No tests planned. "
            "Introduce factory and adapter abstractions. "
            "Use mocks extensively."
        ),
        "tech_stack": "microservice, distributed, scalable, enterprise",
        "architecture": "abstract layered architecture",
    }
    resp = client.post("/api/specs/constitutional-validation", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_compliant"] is False
    assert isinstance(data.get("violations", []), list)
    assert len(data.get("violations", [])) >= 1


def _create_spec(client):
    spec_body = {
        "title": "Spec-Kit Workflow Test",
        "description": "Testing spec-kit workflow phases",
        "content": "Initial content",
        "tags": ["test", "spec-kit"],
    }
    resp = client.post("/api/specs", json=spec_body)
    assert resp.status_code == 200
    return resp.json()


def test_specify_phase_updates_branch_and_feature(client):
    spec = _create_spec(client)
    spec_id = spec["id"]

    req = {"requirements": "As a user, I need a feature."}
    resp = client.post(f"/api/specs/{spec_id}/specify", json=req)
    assert resp.status_code == 200
    data = resp.json()
    updated = data["spec"]

    assert updated["phase"] == "specification"
    assert updated["specification"] == req["requirements"]

    # feature_number should be a 3-digit string; branch should start with it
    feat = updated.get("feature_number")
    branch = updated.get("branch_name")
    assert isinstance(feat, str) and len(feat) == 3 and feat.isdigit()
    assert isinstance(branch, str) and branch.startswith(f"{feat}-")


def _default_customization():
    return {
        "customer_scenario": "Implement MVP",
        "brand_theme": "Default",
        "primary_color": "#3b82f6",
        "company_name": "Acme",
        "industry": "Tech",
        "use_case": "Implementation",
        "additional_requirements": "",
        "use_mcp_tools": False,
        "use_a2a": False,
        "owner": "",
        "repo": "",
    }


@pytest.mark.parametrize("agent", ["github-copilot", "codex-cli"])
def test_assign_to_supported_agents_without_network(client, agent):
    spec = _create_spec(client)
    spec_id = spec["id"]

    body = {
        "agent_id": agent,
        "api_key": "fake",  # not used for these agents
        "template_id": "T1",
        "customization": _default_customization(),
        "mode": "breakdown",
    }
    resp = client.post(f"/api/specs/{spec_id}/assign", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["agent"] == agent

