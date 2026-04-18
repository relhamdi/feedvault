import { getFeeds } from '@/api/client'
import { useQuery } from '@tanstack/react-query'

export const useFeeds = (source_id?: number) =>
    useQuery({
        queryKey: ['feeds', source_id],
        queryFn: () => getFeeds(source_id),
        enabled: source_id !== undefined,
    })