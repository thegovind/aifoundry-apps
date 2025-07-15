import { Template } from '../App'
import { Star, GitFork, Settings, ExternalLink } from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Link } from 'react-router-dom'

interface TemplateCardProps {
  template: Template
}

export function TemplateCard({ template }: TemplateCardProps) {
  return (
    <article className="bg-figma-dark-gray border border-figma-medium-gray rounded-lg overflow-hidden hover:shadow-xl hover:shadow-figma-medium-gray/20 transition-all duration-200 group flex flex-col h-full">
      <div className="h-16 bg-gradient-to-br from-figma-medium-gray to-figma-light-gray flex items-center justify-center">
        <span className="text-2xl">{template.icon}</span>
      </div>
      
      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" className="text-xs font-medium px-1.5 py-0.5 bg-figma-medium-gray text-figma-text-secondary border-figma-light-gray">
            Experiment
          </Badge>
        </div>
        
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-base font-medium text-figma-text-primary group-hover:text-figma-text-primary transition-colors flex-1">
            {template.title}
          </h3>
          <Button variant="ghost" size="sm" className="text-figma-text-primary hover:text-white hover:bg-figma-light-gray p-1 h-6 w-6" asChild>
            <a href={template.github_url} target="_blank" rel="noopener noreferrer" className="flex items-center">
              <ExternalLink className="h-3 w-3" />
            </a>
          </Button>
        </div>
        
        <p className="text-figma-text-secondary text-xs leading-relaxed mb-4 flex-1">
          {template.description}
        </p>
        
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3 text-xs text-figma-text-secondary">
            {template.star_count > 0 && (
              <div className="flex items-center space-x-1">
                <Star className="h-3 w-3" />
                <span>{template.star_count}</span>
              </div>
            )}
            {template.fork_count > 0 && (
              <div className="flex items-center space-x-1">
                <GitFork className="h-3 w-3" />
                <span>{template.fork_count}</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="mt-auto">
          <Button size="sm" className="w-full bg-white text-black hover:bg-gray-800 hover:text-white font-medium transition-colors" asChild>
            <Link to={`/template/${template.id}`} className="flex items-center justify-center">
              <Settings className="h-3 w-3 mr-2" />
              <span className="text-xs">Configure for SWE Agents</span>
            </Link>
          </Button>
        </div>
      </div>
    </article>
  )
}
