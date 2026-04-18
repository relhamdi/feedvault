import { scrape } from '@/api/client'
import { ItemGrid } from '@/components/items/ItemGrid'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useFeeds } from '@/hooks/useFeeds'
import { useQueryClient } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'
import { useState } from 'react'

export function FeedTabs({ sourceId }: { sourceId: number }) {
  const { data: feeds, isLoading } = useFeeds(sourceId)
  const [scrapingFeedId, setScrapingFeedId] = useState<number | null>(null)
  const queryClient = useQueryClient()

  if (isLoading) return <p className="p-4 text-muted-foreground">Loading feeds...</p>
  if (!feeds?.length) return <p className="p-4 text-muted-foreground">No feeds for this source.</p>

  const handleScrape = async (feedId: number) => {
    setScrapingFeedId(feedId)
    try {
      await scrape(feedId)
      // invalidate items cache for this feed so grid refreshes
      queryClient.invalidateQueries({ queryKey: ['items', feedId] })
    } finally {
      setScrapingFeedId(null)
    }
  }

  return (
    <Tabs defaultValue={String(feeds[0].id)} className="flex h-full flex-col">
      <div className="flex items-center gap-2 border-b px-4">
        <TabsList className="h-12 bg-transparent p-0">
          {feeds.map(feed => (
            <TabsTrigger
              key={feed.id}
              value={String(feed.id)}
              className="h-12 rounded-none border-b-2 border-transparent px-4 data-[state=active]:border-primary data-[state=active]:bg-transparent"
            >
              {feed.name}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>

      {feeds.map(feed => (
        <TabsContent
          key={feed.id}
          value={String(feed.id)}
          className="flex h-full flex-col"
        >
          <div className="flex h-full flex-col">
            {/* feed toolbar */}
            <div className="flex items-center justify-between border-b px-4 py-2">
              <span className="text-sm text-muted-foreground">
                {feed.last_scraped_at
                  ? `Last scraped: ${new Date(feed.last_scraped_at).toLocaleString()}`
                  : 'Never scraped'}
              </span>
              <Button
                size="sm"
                variant="outline"
                disabled={scrapingFeedId === feed.id}
                onClick={() => handleScrape(feed.id)}
              >
                <RefreshCw
                  className={`mr-2 h-3 w-3 ${scrapingFeedId === feed.id ? 'animate-spin' : ''}`}
                />
                {scrapingFeedId === feed.id ? 'Scraping...' : 'Scrape'}
              </Button>
            </div>

            <ItemGrid feedId={feed.id} />
          </div>
        </TabsContent>
      ))}
    </Tabs>
  )
}