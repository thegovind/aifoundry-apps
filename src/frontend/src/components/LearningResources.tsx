import { ExternalLink, BookOpen, FileText } from 'lucide-react'
import { Button } from './ui/button'

export function LearningResources() {
  const resources = [
    {
      id: 'azure-ai-fundamentals',
      title: 'Azure AI Fundamentals',
      description: 'Learn the fundamentals of artificial intelligence (AI) and how to implement AI solutions on Azure.',
      url: 'https://docs.microsoft.com/learn/paths/get-started-with-artificial-intelligence-on-azure/',
      type: 'Learning Path',
      icon: BookOpen
    },
    {
      id: 'openai-service',
      title: 'Azure OpenAI Service',
      description: 'Explore Azure OpenAI Service and learn how to integrate powerful AI models into your applications.',
      url: 'https://docs.microsoft.com/azure/cognitive-services/openai/',
      type: 'Documentation',
      icon: FileText
    }
  ]

  return (
    <section className="py-16 bg-white dark:bg-figma-medium-gray">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
          Learning Resources
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {resources.map((resource) => {
            const IconComponent = resource.icon
            return (
              <div key={resource.id} className="bg-white dark:bg-figma-dark-gray border border-gray-200 dark:border-figma-light-gray rounded-lg p-6 hover:shadow-xl hover:shadow-gray-200/20 dark:hover:shadow-gray-900/20 transition-shadow">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <IconComponent className="h-8 w-8 text-figma-text-secondary dark:text-figma-text-secondary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{resource.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">{resource.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">{resource.type}</span>
                      <Button variant="outline" size="sm" className="border-figma-light-gray dark:border-figma-light-gray text-figma-text-secondary dark:text-figma-text-secondary hover:bg-figma-light-gray dark:hover:bg-figma-light-gray" asChild>
                        <a href={resource.url} target="_blank" rel="noopener noreferrer">
                          <ExternalLink className="h-4 w-4 mr-2" />
                          Learn More
                        </a>
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
