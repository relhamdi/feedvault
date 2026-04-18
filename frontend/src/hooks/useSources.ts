import { getSources } from '@/api/client'
import { useQuery } from '@tanstack/react-query'

export const useSources = () =>
    useQuery({
        queryKey: ['sources'],
        queryFn: getSources,
    })