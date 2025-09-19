import { ArrowRight, Zap, Settings } from 'lucide-react'
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
            Build high-quality software faster with Spec-Driven Development - where specifications become executable
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Spec-Kit: now single column width */}
          <Card className="bg-figma-medium-gray border-figma-light-gray hover:border-emerald-400/40 transition-all duration-300 transform hover:scale-[1.005] shadow-lg hover:shadow-emerald-400/10">
            <CardHeader className="text-center pb-4">
              <div className="w-20 h-20 bg-figma-black rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg ring-2 ring-emerald-400/40">
                <span className="text-6xl drop-shadow-sm" aria-hidden>🌱</span>
              </div>
              <CardTitle className="text-2xl text-figma-text-primary mb-2">Specs</CardTitle>
              <CardDescription className="text-figma-text-secondary text-base">
                <a href="https://github.com/github/spec-kit" target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300 underline">Spec-Kit</a> inspired approach to Spec-Driven Development that transforms specs into apps and agents
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              {/* Condensed step showcase */}
              <div className="bg-figma-black/60 rounded-lg p-4 mb-4">
                <div className="grid grid-cols-1 gap-2 text-left">
                  <div className="rounded-md border border-emerald-500/20 bg-emerald-500/5 p-3 hover:border-emerald-400/40 transition-colors">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 bg-emerald-500/20 rounded-full flex items-center justify-center">
                        <span className="text-emerald-300 text-xs font-bold">1</span>
                      </div>
                      <span className="text-emerald-300 font-semibold text-sm">/specify</span>
                    </div>
                    <div className="text-xs text-figma-text-secondary">Define problem space and outcomes</div>
                  </div>
                  <div className="rounded-md border border-emerald-500/20 bg-emerald-500/5 p-3 hover:border-emerald-400/40 transition-colors">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 bg-emerald-500/20 rounded-full flex items-center justify-center">
                        <span className="text-emerald-300 text-xs font-bold">2</span>
                      </div>
                      <span className="text-emerald-300 font-semibold text-sm">/plan</span>
                    </div>
                    <div className="text-xs text-figma-text-secondary">Design architecture and contracts</div>
                  </div>
                  <div className="rounded-md border border-emerald-500/20 bg-emerald-500/5 p-3 hover:border-emerald-400/40 transition-colors">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-6 h-6 bg-emerald-500/20 rounded-full flex items-center justify-center">
                        <span className="text-emerald-300 text-xs font-bold">3</span>
                      </div>
                      <span className="text-emerald-300 font-semibold text-sm">/tasks</span>
                    </div>
                    <div className="text-xs text-figma-text-secondary">Break down into actionable tasks</div>
                  </div>
                </div>
              </div>
              <Button asChild className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white hover:from-emerald-600 hover:to-green-700 border-0 shadow-lg hover:shadow-xl transition-all duration-300 font-medium py-3">
                <Link to="/specs" className="flex items-center justify-center">
                  Start Spec-Driven Development
                  <ArrowRight className="ml-2 h-5 w-5" />
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
              <Button asChild className="w-full bg-white text-black hover:bg-gray-800 hover:text-white border border-gray-300 hover:border-gray-800 transition-colors py-3">
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
              <Button asChild className="w-full bg-white text-black hover:bg-gray-800 hover:text-white border border-gray-300 hover:border-gray-800 transition-colors py-3">
                <Link to="/patterns" className="flex items-center justify-center">
                  Design Patterns
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-figma-medium-gray border-figma-light-gray hover:border-purple-400/40 transition-all duration-300 transform hover:scale-[1.005] shadow-lg hover:shadow-purple-400/10">
            <CardHeader className="text-center pb-4">
              <div className="w-16 h-16 bg-purple-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl" aria-hidden>🧠</span>
              </div>
              <CardTitle className="text-2xl text-figma-text-primary flex items-center justify-center gap-2">
                Post-training with RL
                <span className="text-sm bg-yellow-600/20 text-yellow-400 px-2 py-1 rounded-full" title="Work in Progress">WIP</span>
              </CardTitle>
              <CardDescription className="text-figma-text-secondary">
                Optimize well-defined workflows with RL on small language models using GRPO and post-training techniques
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-sm text-figma-text-secondary mb-6 space-y-2">
                <li>• SFT warmup training</li>
                <li>• GRPO optimization</li>
                <li>• Azure ML deployment</li>
                <li>• Phi-4 & Unsloth integration</li>
              </ul>
              <Button asChild className="w-full bg-gradient-to-r from-purple-500 to-purple-600 text-white hover:from-purple-600 hover:to-purple-700 border-0 shadow-lg hover:shadow-xl transition-all duration-300 font-medium py-3">
                <Link to="/post-training" className="flex items-center justify-center">
                  Start Post-training
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
