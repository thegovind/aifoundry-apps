import { Template } from '../App'
import { TemplateCard } from './TemplateCard'

interface FeaturedTemplatesProps {
  templates: Template[]
}

export function FeaturedTemplates({ templates }: FeaturedTemplatesProps) {
  return (
    <section className="py-20 bg-figma-dark-gray">
      <div className="max-w-[1600px] mx-auto px-6 lg:px-8">
        <h2 className="text-3xl font-light text-figma-text-primary mb-12">
          Featured AI templates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {templates.map((template) => (
            <TemplateCard key={template.id} template={template} />
          ))}
        </div>
      </div>
    </section>
  )
}
