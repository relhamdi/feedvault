import type { Feed, Item, Source } from '@/types'
import axios from 'axios'

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
})

// Sources
export const getSources = () =>
    api.get<Source[]>('/sources/').then(r => r.data)

export const getSource = (id: number) =>
    api.get<Source>(`/sources/${id}`).then(r => r.data)

// Feeds
export const getFeeds = (source_id?: number) =>
    api.get<Feed[]>('/feeds/', { params: { source_id } }).then(r => r.data)

// Items
export const getItems = (params: {
    feed_id?: number
    is_read?: boolean
    is_favorite?: boolean
    is_nsfw?: boolean
    is_public?: boolean
    sort_by?: string
    sort_order?: string
    limit?: number
    offset?: number
}) => api.get<Item[]>('/items/', { params }).then(r => r.data)

export const updateItem = (id: number, data: Partial<Item>) =>
    api.patch<Item>(`/items/${id}`, data).then(r => r.data)

// Scrape
export const scrape = (feed_id: number, mode = 'INCREMENTAL') =>
    api.post('/scrape/', { feed_id, mode }).then(r => r.data)