import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'
import { ExternalLink } from 'lucide-react'
import { Button } from './ui/button'
import { Link } from 'react-router-dom'

interface PatternCardProps {
  pattern: {
    id: string
    title: string
    description: string
    mermaidCode: string
    azureFoundryUrl: string
  }
}

export function PatternCard({ pattern }: PatternCardProps) {
  const mermaidRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (mermaidRef.current) {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'base',
        themeVariables: {
          primaryColor: '#424242',
          primaryTextColor: '#D4D4D4',
          primaryBorderColor: '#424242',
          lineColor: '#424242',
          secondaryColor: '#292929',
          tertiaryColor: '#141414'
        },
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true
        }
      })
      
      const renderDiagram = async () => {
        try {
          const result = await mermaid.render(`mermaid-${pattern.id}`, pattern.mermaidCode)
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = result.svg
          }
        } catch (error) {
          console.error('Mermaid rendering error:', error)
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = `<pre class="text-figma-text-secondary text-sm">${pattern.mermaidCode}</pre>`
          }
        }
      }
      
      renderDiagram()
    }
  }, [pattern.id, pattern.mermaidCode])

  return (
    <div className="bg-figma-medium-gray border border-figma-light-gray rounded-lg p-6 hover:border-figma-text-secondary transition-colors flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-xl font-semibold text-figma-text-primary mb-2">{pattern.title}</h3>
        <p className="text-figma-text-secondary text-sm leading-relaxed">{pattern.description}</p>
      </div>
      
      <div className="mb-6 bg-figma-dark-gray rounded-lg p-6 overflow-x-auto flex-grow">
        <div ref={mermaidRef} className="flex justify-center min-h-[250px] items-center" />
      </div>
      
      <div className="flex justify-end mt-auto">
        <Button variant="outline" size="sm" className="text-black bg-white border-gray-300 hover:bg-gray-800 hover:text-white hover:border-gray-800 transition-colors" asChild>
          <Link to={`/pattern/${pattern.id}`} className="flex items-center">
            <ExternalLink className="h-4 w-4 mr-1" />
            Configure for your scenario
          </Link>
        </Button>
      </div>
    </div>
  )
}
