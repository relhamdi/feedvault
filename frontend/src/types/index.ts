export interface Source {
    id: number
    slug: string
    name: string
    color: string | null
    icon_path: string | null
    source_type: "RSS" | "API" | "SCRAPER"
    base_url: string
    default_tags: string[]
    is_active: boolean
    last_scraped_at: string | null
    created_at: string
    updated_at: string
}

export interface Feed {
    id: number
    name: string
    source_id: number
    url: string
    icon_path: string | null
    color: string | null
    default_tags: string[]
    is_active: boolean
    last_scraped_at: string | null
    params: Record<string, unknown>
    created_at: string
    updated_at: string
}

export interface Item {
    id: number
    feed_id: number
    author_id: number | null
    external_id: string
    title: string
    url: string
    description: string | null
    summary: string | null
    thumbnail_path: string | null
    tags: string[]
    stats: Record<string, number>
    meta: Record<string, unknown>
    raw_extra: Record<string, unknown>
    is_read: boolean
    is_favorite: boolean
    is_nsfw: boolean
    is_public: boolean
    source_published_at: string
    source_updated_at: string
    scraped_at: string
    last_scraped_at: string
    created_at: string
    updated_at: string
}

export interface Author {
    id: number
    external_id: string
    source_id: number
    name: string
    url: string | null
    icon_url: string | null
}

export interface Category {
    id: number
    name: string
    parent_id: number | null
    source_id: number | null
}