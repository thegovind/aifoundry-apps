import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog'
import { Button } from './ui/button'
import { X, ExternalLink } from 'lucide-react'

interface ConstitutionViewerProps {
  isOpen: boolean
  onClose: () => void
  constitution: string
  projectName?: string
}

export function ConstitutionViewer({ isOpen, onClose, constitution, projectName }: ConstitutionViewerProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] bg-figma-medium-gray border-figma-light-gray">
        <DialogHeader>
          <DialogTitle className="text-figma-text-primary flex items-center gap-2">
            <span>⚖️</span>
            {projectName ? `${projectName} Constitution` : 'Constitutional Framework'}
          </DialogTitle>
          <DialogDescription className="text-figma-text-secondary">
            Constitutional framework based on <a href="https://github.com/github/spec-kit" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline inline-flex items-center gap-1">
              spec-kit methodology <ExternalLink className="h-3 w-3" />
            </a> that governs spec-driven development compliance
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-y-auto">
          <div className="bg-figma-dark-gray rounded-md p-6">
            <div 
              className="prose prose-invert prose-sm max-w-none"
              dangerouslySetInnerHTML={{ 
                __html: constitution
                  .replace(/\n/g, '<br>')
                  .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-white mb-4 mt-6">$1</h1>')
                  .replace(/^## (.+)$/gm, '<h2 class="text-xl font-semibold text-white mb-3 mt-5">$2</h2>')
                  .replace(/^### (.+)$/gm, '<h3 class="text-lg font-medium text-white mb-2 mt-4">$3</h3>')
                  .replace(/^\*\*(.+):\*\*$/gm, '<p class="font-semibold text-blue-300 mb-2">$1:</p>')
                  .replace(/^- (.+)$/gm, '<li class="text-figma-text-primary ml-4 mb-1">• $1</li>')
                  .replace(/^\*(.+)\*$/gm, '<p class="italic text-figma-text-secondary mb-2">$1</p>')
                  .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">$1</a>')
              }}
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-figma-light-gray">
          <div className="text-xs text-figma-text-secondary">
            Read-only view • Based on spec-kit constitutional framework
          </div>
          <Button
            variant="outline"
            onClick={onClose}
            className="border-figma-light-gray text-figma-text-primary hover:bg-figma-light-gray/20 hover:text-white"
          >
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
