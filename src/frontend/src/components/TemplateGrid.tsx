import { Template } from '../App'
import { TemplateCard } from './TemplateCard'

interface TemplateGridProps {
  templates: Template[]
  loading: boolean
}

export function TemplateGrid({ templates, loading }: TemplateGridProps) {
  if (loading) {
    return (
      <section className="py-16 bg-figma-medium-gray">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-figma-dark-gray rounded-lg h-48 animate-pulse"></div>
            ))}
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="py-16 bg-figma-medium-gray">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {templates.map((template) => (
            <TemplateCard key={template.id} template={template} />
          ))}
        </div>
      </div>
    </section>
  )
}
