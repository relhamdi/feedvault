import { useItems } from '@/hooks/useItems'
import { ItemCard } from '@/components/items/ItemCard'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useState } from 'react'
import { ItemModal } from '@/components/items/ItemModal'
import type { Item } from '@/types'

export function ItemGrid({ feedId }: { feedId: number }) {
  const { data: items, isLoading } = useItems(feedId)
  const [selectedItem, setSelectedItem] = useState<Item | null>(null)

  if (isLoading) return <p className="p-4 text-muted-foreground">Loading items...</p>
  if (!items?.length) return <p className="p-4 text-muted-foreground">No items yet — try scraping.</p>

  return (
    <>
      <ScrollArea className="h-full">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-4 p-4">
          {items.map(item => (
            <ItemCard
              key={item.id}
              item={item}
              onClick={() => setSelectedItem(item)}
            />
          ))}
        </div>
      </ScrollArea>

      <ItemModal
        item={selectedItem}
        open={selectedItem !== null}
        onClose={() => setSelectedItem(null)}
      />
    </>
  )
}