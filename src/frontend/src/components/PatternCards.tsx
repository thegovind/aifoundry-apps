import { PatternCard } from './PatternCard'
import { ExternalLink } from 'lucide-react'

export function PatternCards() {
  const patterns = [
    {
      id: 'prompt-chaining',
      title: 'Prompt Chaining',
      description: 'Sequential processing where the output of one agent becomes the input for the next, with conditional gates and error handling for complex multi-step workflows.',
      azureFoundryUrl: 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview',
      mermaidCode: `
        flowchart LR
          In[In] --> A[🧠]
          A --> |Output 1| Gate{Gate}
          Gate --> |Pass| B[🧠]
          Gate --> |Fail| Exit[Exit]
          B --> |Output 2| C[🧠]
          C --> Out[Out]
          
          style In fill:#292929,stroke:#424242
          style Out fill:#141414,stroke:#424242
          style Exit fill:#141414,stroke:#424242
          style Gate fill:#292929,stroke:#424242
          style A fill:#424242,stroke:#D4D4D4
          style B fill:#424242,stroke:#D4D4D4
          style C fill:#424242,stroke:#D4D4D4
      `
    },
    {
      id: 'routing',
      title: 'Routing',
      description: 'Intelligent request routing where a central router agent directs tasks to specialized agents based on content analysis and agent capabilities.',
      azureFoundryUrl: 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview',
      mermaidCode: `
        flowchart TD
          In[In] --> Router[🧠<br/>Router]
          Router --> A[🧠]
          Router --> B[🧠]
          Router --> C[🧠]
          Router --> D[🧠]
          A --> Out[Out]
          B --> Out
          C --> Out
          D --> Out
          
          style In fill:#292929,stroke:#424242
          style Out fill:#141414,stroke:#424242
          style Router fill:#424242,stroke:#D4D4D4
          style A fill:#424242,stroke:#D4D4D4
          style B fill:#424242,stroke:#D4D4D4
          style C fill:#424242,stroke:#D4D4D4
          style D fill:#424242,stroke:#D4D4D4
      `
    },
    {
      id: 'parallelization',
      title: 'Parallelization',
      description: 'Concurrent processing where multiple agents work simultaneously on different aspects of a task, with results aggregated for comprehensive output.',
      azureFoundryUrl: 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview',
      mermaidCode: `
        flowchart LR
          In[In] --> A[🧠]
          In --> B[🧠]
          In --> C[🧠]
          A --> Agg[Aggregator]
          B --> Agg
          C --> Agg
          Agg --> Out[Out]
          
          style In fill:#292929,stroke:#424242
          style Out fill:#141414,stroke:#424242
          style Agg fill:#292929,stroke:#424242
          style A fill:#424242,stroke:#D4D4D4
          style B fill:#424242,stroke:#D4D4D4
          style C fill:#424242,stroke:#D4D4D4
      `
    },
    {
      id: 'orchestrator',
      title: 'Orchestrator',
      description: 'Complex workflow management where an orchestrator coordinates multiple specialized agents and synthesizes their outputs into cohesive results.',
      azureFoundryUrl: 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview',
      mermaidCode: `
        flowchart TD
          In[In] --> Orch[🧠<br/>Orchestrator]
          Orch --> A[🧠]
          Orch --> B[🧠]
          A --> Synth[🧠<br/>Synthesizer]
          B --> Synth
          Orch --> C[🧠]
          C --> Synth
          Synth --> Out[Out]
          
          style In fill:#292929,stroke:#424242
          style Out fill:#141414,stroke:#424242
          style Orch fill:#424242,stroke:#D4D4D4
          style Synth fill:#424242,stroke:#D4D4D4
          style A fill:#424242,stroke:#D4D4D4
          style B fill:#424242,stroke:#D4D4D4
          style C fill:#424242,stroke:#D4D4D4
      `
    },
    {
      id: 'evaluator-optimizer',
      title: 'Evaluator-optimizer',
      description: 'Iterative improvement system where a generator creates solutions and an evaluator provides feedback, creating a continuous optimization loop.',
      azureFoundryUrl: 'https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview',
      mermaidCode: `
        flowchart TD
          In[In] --> Gen[🧠<br/>Generator]
          Gen --> |Solution| Eval[🧠<br/>Evaluator]
          Eval --> |Accepted| Out[Out]
          Eval --> |Rejected +<br/>Feedback| Gen
          
          style In fill:#292929,stroke:#424242
          style Out fill:#141414,stroke:#424242
          style Gen fill:#424242,stroke:#D4D4D4
          style Eval fill:#424242,stroke:#D4D4D4
      `
    }
  ]

  return (
    <section className="py-8 bg-figma-black">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center mb-8">
          <p className="text-lg text-gray-300 max-w-5xl mx-auto">
            Define your own scenarios that conform to these proven patterns and use{' '}
            <a 
              href="https://learn.microsoft.com/en-us/azure/ai-foundry/agents/overview" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gray-300 underline inline-flex items-center gap-1"
            >
              Azure AI Foundry Agent Service
              <ExternalLink className="h-4 w-4" />
            </a>
            {' '}to build them using SWE Agents.
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {patterns.map((pattern) => (
            <PatternCard key={pattern.id} pattern={pattern} />
          ))}
        </div>
      </div>
    </section>
  )
}
