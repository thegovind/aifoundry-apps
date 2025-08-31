patterns_data = [
    {
        "id": "prompt-chaining",
        "title": "Prompt Chaining Pattern",
        "description": "Sequential processing where the output of one agent becomes the input for the next, with conditional gates and error handling for complex multi-step workflows.",
        "type": "Sequential Processing",
        "use_cases": ["Multi-step workflows", "Data transformation pipelines", "Complex reasoning chains"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "routing", 
        "title": "Routing Pattern",
        "description": "Intelligent request routing where a central router agent directs tasks to specialized agents based on content analysis and agent capabilities.",
        "type": "Request Routing",
        "use_cases": ["Content classification", "Task delegation", "Load balancing"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "parallelization",
        "title": "Parallelization Pattern", 
        "description": "Concurrent processing where multiple agents work simultaneously on different aspects of a task, with results aggregated for comprehensive output.",
        "type": "Concurrent Processing",
        "use_cases": ["Parallel analysis", "Multi-perspective evaluation", "Distributed processing"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "orchestrator",
        "title": "Orchestrator Pattern",
        "description": "Complex workflow management where an orchestrator coordinates multiple specialized agents and synthesizes their outputs into cohesive results.",
        "type": "Workflow Management", 
        "use_cases": ["Complex workflows", "Multi-agent coordination", "Result synthesis"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    },
    {
        "id": "evaluator-optimizer",
        "title": "Evaluator-Optimizer Pattern",
        "description": "Iterative improvement system where a generator creates solutions and an evaluator provides feedback, creating a continuous optimization loop.",
        "type": "Iterative Improvement",
        "use_cases": ["Solution optimization", "Quality improvement", "Iterative refinement"],
        "github_url": "https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview"
    }
]

filter_options_data = {
    "tasks": ["Single-agent", "Multi-agent"],
    "languages": [".NET/C#", "JavaScript", "Python"],
    "collections": ["Microsoft", "Auquan", "Saifr from Fidelity Labs", "SightMachine", "Marquee Insights", "MiHCM"],
    "models": ["GPT-4", "GPT-4 Omni mini", "GPT-4 Turbo"],
    "databases": ["Azure AI Search", "File Search", "Code Interpreter", "Azure Functions"],
    "patterns": ["Prompt Chaining", "Routing", "Parallelization", "Orchestrator", "Evaluator-optimizer"]
}

learning_resources_data = [
    {
        "id": "azure-ai-fundamentals",
        "title": "Azure AI Fundamentals",
        "description": "Learn the fundamentals of artificial intelligence (AI) and how to implement AI solutions on Azure.",
        "url": "https://docs.microsoft.com/learn/paths/get-started-with-artificial-intelligence-on-azure/",
        "type": "Learning Path",
        "icon": "📚"
    },
    {
        "id": "openai-service",
        "title": "Azure OpenAI Service",
        "description": "Explore Azure OpenAI Service and learn how to integrate powerful AI models into your applications.",
        "url": "https://docs.microsoft.com/azure/cognitive-services/openai/",
        "type": "Documentation",
        "icon": "🔧"
    }
]
