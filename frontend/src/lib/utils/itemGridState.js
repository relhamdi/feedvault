import { itemsApi } from '../api/items.js';
import { scrapeApi } from '../api/scrape.js';
import { DEFAULT_ITEMS_LIMIT } from '../config.js';
import { pollJob } from '../stores/scraping.js';
import { toastError, toastInfo, toastSuccess } from '../stores/toast.js';
import { parseComaString } from './format.js';

/**
 * Build filter params from current filter/sort store values.
 * Caller passes the raw store values (not the stores themselves).
 */
export function buildItemParams(filters, sort, offset) {
    const params = {
        limit: DEFAULT_ITEMS_LIMIT,
        offset,
        sort_by: sort.sort_by,
        sort_order: sort.sort_order,
    };
    if (filters.is_read !== null) params.is_read = filters.is_read;
    if (filters.is_favorite !== null) params.is_favorite = filters.is_favorite;
    if (filters.is_nsfw !== null) params.is_nsfw = filters.is_nsfw;
    if (filters.is_public !== null) params.is_public = filters.is_public;
    if (filters.search) params.search = filters.search;
    if (filters.tags) {
        const tags = parseComaString(filters.tags);
        if (tags.length) params.tags = tags;
    }
    return params;
}

/**
 * Toggle is_read on an item and update the local list.
 */
export async function toggleRead(item, items, onSuccess, onError) {
    try {
        const updated = { ...item, is_read: !item.is_read };
        await itemsApi.update(item.id, { is_read: updated.is_read });
        onSuccess(updated);
    } catch (e) {
        console.error('Failed to update item:', e.message);
        toastError(`Failed to update item: ${e.message}`);
        onError?.(e);
    }
}

/**
 * Toggle is_favorite on an item.
 */
export async function toggleFavorite(item, onSuccess, onError) {
    try {
        const updated = { ...item, is_favorite: !item.is_favorite };
        await itemsApi.update(item.id, { is_favorite: updated.is_favorite });
        onSuccess(updated);
    } catch (e) {
        console.error('Failed to update item:', e.message);
        toastError(`Failed to update item: ${e.message}`);
        onError?.(e);
    }
}

/**
 * Refresh a single item via scrape job.
 * Returns a cleanup function.
 */
export async function refreshItem(item, { onStart, onDone, onError }) {
    try {
        const job = await scrapeApi.scrape({
            feed_id: item.feed_id,
            mode: 'FULL',
            external_ids: [item.external_id],
        });
        toastInfo(`Refreshing "${item.title}"...`);
        onStart?.();
        return pollJob(job.id, {
            onDone: async () => {
                const updated = await itemsApi.get(item.id);
                toastSuccess(`"${item.title}" refreshed`);
                onDone(updated);
            },
            onError: (msg) => {
                toastError(`Refresh error: ${msg}`);
                onError?.(msg);
            },
        });
    } catch (e) {
        console.error('Refresh failed:', e.message);
        toastError(`Refresh failed: ${e.message}`);
        onError?.(e.message);
        return null;
    }
}

/**
 * Build context menu items for an item card.
 */
export function buildContextMenuItems({
    item,
    canRefresh,
    onToggleRead,
    onToggleFavorite,
    onRefresh,
}) {
    return [
        {
            label: 'Open in new tab',
            icon: '↗',
            action: () => window.open(item.url, '_blank', 'noopener,noreferrer'),
        },
        { separator: true },
        {
            label: item.is_read ? 'Mark as unread' : 'Mark as read',
            icon: item.is_read ? '○' : '●',
            action: () => onToggleRead(item),
        },
        {
            label: item.is_favorite ? 'Remove from favorites' : 'Add to favorites',
            icon: item.is_favorite ? '♥' : '♡',
            action: () => onToggleFavorite(item),
        },
        ...(canRefresh
            ? [
                  { separator: true },
                  { label: 'Refresh item', icon: '⟳', action: () => onRefresh(item) },
              ]
            : []),
    ];
}
