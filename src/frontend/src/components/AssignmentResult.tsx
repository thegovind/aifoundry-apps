import { useState } from 'react'
import { Badge } from './ui/badge'

interface Props {
  result: any
}

export function AssignmentResult({ result }: Props) {
  const [showRaw, setShowRaw] = useState(false)

  const status: string = result?.status || result?.session_status || 'unknown'
  const agent: string | undefined = result?.agent || result?.agent_id
  const message: string | undefined = result?.message
  const specId: string | undefined = result?.spec_id || result?.template_id
  const sessionId: string | undefined = result?.session_id
  const sessionUrl: string | undefined = result?.session_url || (sessionId ? `https://app.devin.ai/sessions/${sessionId}` : undefined)
  const repoUrl: string | undefined = result?.repository_url || result?.repo_url
  const issueUrl: string | undefined = result?.issue_url

  const badgeVariant =
    status === 'success' ? 'default' : status === 'error' ? 'destructive' : 'secondary'

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <Badge variant={badgeVariant as any} className="capitalize">{status}</Badge>
        {agent && <span className="text-sm text-figma-text-secondary">Agent: <span className="text-white">{agent}</span></span>}
        {specId && <span className="text-sm text-figma-text-secondary">Spec: <span className="text-white">{specId}</span></span>}
      </div>

      {message && (
        <div className="text-sm text-figma-text-secondary bg-figma-dark-gray border border-figma-light-gray rounded p-3">
          {message}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4">
        {sessionUrl && (
          <a
            href={sessionUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1.5 rounded bg-white text-black hover:bg-gray-200 text-sm font-medium"
          >
            Open Devin Session
          </a>
        )}
        {repoUrl && (
          <a href={repoUrl} target="_blank" rel="noopener noreferrer" className="text-sm underline text-blue-400 hover:text-blue-300">
            Open Repository
          </a>
        )}
        {issueUrl && (
          <a href={issueUrl} target="_blank" rel="noopener noreferrer" className="text-sm underline text-blue-400 hover:text-blue-300">
            Open Issue
          </a>
        )}
        <button
          type="button"
          className="text-sm underline text-figma-text-secondary hover:text-white"
          onClick={() => setShowRaw(x => !x)}
        >
          {showRaw ? 'Hide raw JSON' : 'Show raw JSON'}
        </button>
      </div>

      {showRaw && (
        <pre className="text-sm text-figma-text-secondary whitespace-pre-wrap bg-figma-dark-gray p-4 rounded border border-figma-light-gray overflow-x-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  )
}

export default AssignmentResult
