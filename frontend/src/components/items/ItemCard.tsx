import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { Item } from '@/types'

interface ItemCardProps {
  item: Item
  onClick: () => void
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

function truncate(text: string | null, max: number) {
  if (!text) return null
  return text.length > max ? text.slice(0, max) + '…' : text
}

export function ItemCard({ item, onClick }: ItemCardProps) {
  const preview = truncate(item.summary ?? item.description, 100)

  return (
    <Card
      onClick={onClick}
      className={`cursor-pointer transition-opacity hover:opacity-90 ${!item.is_read ? '' : 'opacity-50'}`}
    >
      {/* thumbnail */}
      {item.thumbnail_path && (
        <div className="aspect-[3/2] w-full overflow-hidden rounded-t-lg bg-muted">
          <img
            src={`http://localhost:8000/media/${item.thumbnail_path}`}
            alt={item.title}
            className="h-full w-full object-cover"
            onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
          />
        </div>
      )}

      <CardContent className="flex flex-col gap-2 p-3">
        {/* badges */}
        <div className="flex flex-wrap gap-1">
          {item.is_favorite && (
            <Badge variant="secondary" className="text-yellow-500">★ Favorite</Badge>
          )}
          {item.is_nsfw && (
            <Badge variant="destructive">NSFW</Badge>
          )}
          {!item.is_public && (
            <Badge variant="outline">Private</Badge>
          )}
        </div>

        {/* title */}
        <p className="text-sm font-semibold leading-tight line-clamp-2">{item.title}</p>

        {/* preview text */}
        {preview && (
          <p className="text-xs text-muted-foreground line-clamp-3">{preview}</p>
        )}

        {/* tags */}
        {item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {item.tags.slice(0, 3).map(tag => (
              <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
            ))}
            {item.tags.length > 3 && (
              <Badge variant="outline" className="text-xs">+{item.tags.length - 3}</Badge>
            )}
          </div>
        )}

        {/* date + author */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{formatDate(item.source_updated_at)}</span>
        </div>
      </CardContent>
    </Card>
  )
}