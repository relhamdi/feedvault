import { Badge } from '@/components/ui/badge'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { Item } from '@/types'

interface ItemModalProps {
  item: Item | null
  open: boolean
  onClose: () => void
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function ItemModal({ item, open, onClose }: ItemModalProps) {
  if (!item) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="flex max-h-[90vh] max-w-2xl flex-col gap-0 p-0">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle className="text-lg leading-snug">{item.title}</DialogTitle>
        </DialogHeader>

        <ScrollArea className="flex-1 px-6 pb-6">
          <div className="flex flex-col gap-4 pt-4">
            {/* thumbnail */}
            {item.thumbnail_path && (
              <img
                src={`http://localhost:8000/media/${item.thumbnail_path}`}
                alt={item.title}
                className="w-full rounded-lg object-cover"
                onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            )}

            {/* badges */}
            <div className="flex flex-wrap gap-2">
              {item.is_favorite && <Badge variant="secondary" className="text-yellow-500">★ Favorite</Badge>}
              {item.is_nsfw && <Badge variant="destructive">NSFW</Badge>}
              {!item.is_public && <Badge variant="outline">Private</Badge>}
              {!item.is_read && <Badge variant="outline">Unread</Badge>}
            </div>

            {/* dates */}
            <div className="flex flex-col gap-1 text-xs text-muted-foreground">
              <span>Published: {formatDate(item.source_published_at)}</span>
              <span>Updated: {formatDate(item.source_updated_at)}</span>
            </div>

            {/* description */}
            {item.description && (
              <p className="text-sm text-muted-foreground italic">{item.description}</p>
            )}

            {/* summary */}
            {item.summary && (
              <div
                className="prose prose-sm max-w-none text-sm"
                dangerouslySetInnerHTML={{ __html: item.summary }}
              />
            )}

            {/* stats */}
            {Object.keys(item.stats).length > 0 && (
              <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                {Object.entries(item.stats).map(([key, val]) => (
                  <span key={key}>{key}: {val}</span>
                ))}
              </div>
            )}

            {/* metadata */}
            {Object.keys(item.meta).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {Object.entries(item.meta).map(([key, val]) => (
                  <Badge key={key} variant="outline" className="text-xs">
                    {key}: {String(val)}
                  </Badge>
                ))}
              </div>
            )}

            {/* tags */}
            {item.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {item.tags.map(tag => (
                  <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
                ))}
              </div>
            )}

            {/* external link */}
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary underline underline-offset-2"
            >
              View on source →
            </a>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}