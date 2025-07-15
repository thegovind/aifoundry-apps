import { ArrowLeft } from 'lucide-react'
import { Button } from './ui/button'
import { FeaturedTemplates } from './FeaturedTemplates'
import { FilterSection } from './FilterSection'
import { TemplateGrid } from './TemplateGrid'
import { Link } from 'react-router-dom'
import { Template, FilterOptions } from '../App'

interface TemplatesPageProps {
  templates: Template[]
  featuredTemplates: Template[]
  filterOptions: FilterOptions
  filters: {
    search: string
    task: string
    language: string
    collection: string
    model: string
    database: string
    sort: string
  }
  onFiltersChange: (filters: Partial<{
    search: string
    task: string
    language: string
    collection: string
    model: string
    database: string
    sort: string
  }>) => void
  loading: boolean
}

export function TemplatesPage({ 
  templates, 
  featuredTemplates, 
  filterOptions, 
  filters, 
  onFiltersChange, 
  loading 
}: TemplatesPageProps) {
  return (
    <div className="min-h-screen bg-figma-black">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        <div className="flex items-center mb-8">
          <Button variant="ghost" asChild className="mr-4">
            <Link to="/" className="flex items-center">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Link>
          </Button>
          <h1 className="text-3xl font-bold text-figma-text-primary">
            AI Solution Templates
          </h1>
        </div>
        <FeaturedTemplates templates={featuredTemplates} />
        <FilterSection 
          filterOptions={filterOptions}
          filters={filters}
          onFiltersChange={onFiltersChange}
        />
        <TemplateGrid templates={templates} loading={loading} />
      </div>
    </div>
  )
}
