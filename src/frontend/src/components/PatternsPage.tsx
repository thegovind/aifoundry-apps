import { ArrowLeft } from 'lucide-react'
import { Button } from './ui/button'
import { PatternCards } from './PatternCards'
import { Link } from 'react-router-dom'

export function PatternsPage() {
  return (
    <div className="min-h-screen bg-figma-black">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-4">
        <div className="flex items-center mb-4">
          <Button variant="ghost" asChild className="mr-4">
            <Link to="/" className="flex items-center">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Link>
          </Button>
          <h1 className="text-3xl font-bold text-figma-text-primary">
            AI Agent Patterns
          </h1>
        </div>
        <PatternCards />
      </div>
    </div>
  )
}
