import { ArrowRight, Zap, Settings, FileText } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Link } from 'react-router-dom'

export function LandingPage() {
  return (
    <section className="py-12 bg-figma-black">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-figma-text-primary mb-4">
            Build AI Solutions with SWE Agents
          </h1>
          <p className="text-xl text-figma-text-secondary max-w-3xl mx-auto">
            Customize AI solution accelerators through spec-driven development and context engineering for your scenario
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <Card className="bg-figma-medium-gray border-figma-light-gray hover:border-figma-text-secondary transition-colors">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 bg-orange-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText className="h-8 w-8 text-orange-400" />
              </div>
              <CardTitle className="text-2xl text-figma-text-primary">Customize Specs</CardTitle>
              <CardDescription className="text-figma-text-secondary">
                Write detailed specifications with markdown and break them down into actionable tasks
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-sm text-figma-text-secondary mb-6 space-y-2">
                <li>• Markdown specification editor</li>
                <li>• AI-enhanced task breakdown</li>
                <li>• SWE agent assignment</li>
              </ul>
              <Button asChild className="w-full bg-white text-black hover:bg-gray-800 hover:text-white border border-gray-300 hover:border-gray-800 transition-colors">
                <Link to="/specs" className="flex items-center justify-center">
                  Customize Specs
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-figma-medium-gray border-figma-light-gray hover:border-figma-text-secondary transition-colors">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Settings className="h-8 w-8 text-green-400" />
              </div>
              <CardTitle className="text-2xl text-figma-text-primary">Configure Templates</CardTitle>
              <CardDescription className="text-figma-text-secondary">
                Browse and configure pre-built AI solution templates for rapid deployment
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-sm text-figma-text-secondary mb-6 space-y-2">
                <li>• Ready-to-use AI solutions</li>
                <li>• Multiple languages & frameworks</li>
                <li>• SWE agent integration</li>
              </ul>
              <Button asChild className="w-full bg-white text-black hover:bg-gray-800 hover:text-white border border-gray-300 hover:border-gray-800 transition-colors">
                <Link to="/templates" className="flex items-center justify-center">
                  Configure Templates
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-figma-medium-gray border-figma-light-gray hover:border-figma-text-secondary transition-colors">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="h-8 w-8 text-blue-400" />
              </div>
              <CardTitle className="text-2xl text-figma-text-primary flex items-center justify-center gap-2">
                Design Patterns
                <span className="text-sm bg-yellow-600/20 text-yellow-400 px-2 py-1 rounded-full" title="Work in Progress">WIP</span>
              </CardTitle>
              <CardDescription className="text-figma-text-secondary">
                Start with proven AI agent patterns and tailor them to your specific workflow
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-sm text-figma-text-secondary mb-6 space-y-2">
                <li>• Prompt Chaining & Routing</li>
                <li>• Parallelization & Orchestration</li>
                <li>• Evaluator-Optimizer patterns</li>
              </ul>
              <Button asChild className="w-full bg-white text-black hover:bg-gray-800 hover:text-white border border-gray-300 hover:border-gray-800 transition-colors">
                <Link to="/patterns" className="flex items-center justify-center">
                  Design Patterns
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  )
}
