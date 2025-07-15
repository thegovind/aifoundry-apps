import { FilterOptions } from '../App'
import { Search } from 'lucide-react'
import { Input } from './ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'

interface FilterSectionProps {
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
}

export function FilterSection({ filterOptions, filters, onFiltersChange }: FilterSectionProps) {
  return (
    <section className="py-12 bg-figma-black border-t border-figma-medium-gray">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-6 lg:space-y-0 mb-8">
          <h2 className="text-2xl font-light text-figma-text-primary">Filter by</h2>
          
          <div className="flex items-center space-x-6">
            <span className="text-sm text-figma-text-secondary">Showing 52 templates</span>
            <Select value={filters.sort} onValueChange={(value) => onFiltersChange({ sort: value })}>
              <SelectTrigger className="w-40 border-figma-light-gray bg-figma-medium-gray text-figma-text-primary">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-figma-medium-gray border-figma-light-gray text-figma-text-primary">
                <SelectItem value="Most Popular" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">Most Popular</SelectItem>
                <SelectItem value="Most Recent" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">Most Recent</SelectItem>
                <SelectItem value="Most Forked" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">Most Forked</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          <div className="lg:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-figma-text-secondary" />
              <Input
                placeholder="Search templates"
                value={filters.search}
                onChange={(e) => onFiltersChange({ search: e.target.value })}
                className="pl-10 border-figma-light-gray bg-figma-medium-gray text-figma-text-primary placeholder-figma-text-secondary focus:border-figma-light-gray"
              />
            </div>
          </div>
          
          <Select value={filters.task} onValueChange={(value) => onFiltersChange({ task: value })}>
            <SelectTrigger className="border-figma-light-gray bg-figma-medium-gray text-figma-text-primary">
              <SelectValue placeholder="Task" />
            </SelectTrigger>
            <SelectContent className="bg-figma-medium-gray border-figma-light-gray text-figma-text-primary">
              <SelectItem value="all" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">All Tasks</SelectItem>
              {filterOptions.tasks.map((task) => (
                <SelectItem key={task} value={task} className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">{task}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={filters.language} onValueChange={(value) => onFiltersChange({ language: value })}>
            <SelectTrigger className="border-figma-light-gray bg-figma-medium-gray text-figma-text-primary">
              <SelectValue placeholder="Language" />
            </SelectTrigger>
            <SelectContent className="bg-figma-medium-gray border-figma-light-gray text-figma-text-primary">
              <SelectItem value="all" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">All Languages</SelectItem>
              {filterOptions.languages.map((language) => (
                <SelectItem key={language} value={language} className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">{language}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={filters.collection} onValueChange={(value) => onFiltersChange({ collection: value })}>
            <SelectTrigger className="border-figma-light-gray bg-figma-medium-gray text-figma-text-primary">
              <SelectValue placeholder="Collection" />
            </SelectTrigger>
            <SelectContent className="bg-figma-medium-gray border-figma-light-gray text-figma-text-primary">
              <SelectItem value="all" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">All Collections</SelectItem>
              {filterOptions.collections.map((collection) => (
                <SelectItem key={collection} value={collection} className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">{collection}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Select value={filters.model} onValueChange={(value) => onFiltersChange({ model: value })}>
            <SelectTrigger className="border-figma-light-gray bg-figma-medium-gray text-figma-text-primary">
              <SelectValue placeholder="Model" />
            </SelectTrigger>
            <SelectContent className="bg-figma-medium-gray border-figma-light-gray text-figma-text-primary">
              <SelectItem value="all" className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">All Models</SelectItem>
              {filterOptions.models.map((model) => (
                <SelectItem key={model} value={model} className="text-figma-text-primary hover:bg-figma-light-gray focus:bg-figma-light-gray">{model}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </section>
  )
}
