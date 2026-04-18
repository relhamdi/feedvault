import { useQuery } from '@tanstack/react-query'
import { getItems } from '@/api/client'

export const useItems = (feed_id?: number) =>
  useQuery({
    queryKey: ['items', feed_id],
    queryFn: () => getItems({ feed_id, sort_by: 'source_updated_at', sort_order: 'desc', limit: 50 }),
    enabled: feed_id !== undefined,
  })