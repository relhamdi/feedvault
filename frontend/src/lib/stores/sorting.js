import { writable } from 'svelte/store';

function persistedSort(key, defaultValue) {
    const stored = localStorage.getItem(key);
    const initial = stored ? JSON.parse(stored) : defaultValue;
    const store = writable(initial);
    store.subscribe((val) => localStorage.setItem(key, JSON.stringify(val)));
    return store;
}

export const sourceSort = persistedSort('sort:sources', {
    sort_by: 'name',
    sort_order: 'asc',
});

export const feedSort = persistedSort('sort:feeds', {
    sort_by: 'name',
    sort_order: 'asc',
});

export const collectionSort = persistedSort('sort:collections', {
    sort_by: 'name',
    sort_order: 'asc',
});

export const itemSort = persistedSort('sort:items', {
    sort_by: 'source_updated_at',
    sort_order: 'desc',
});

export const SOURCE_SORT_OPTIONS = [
    { value: 'name', label: 'Name' },
    { value: 'last_scraped_at', label: 'Last scraped' },
    { value: 'created_at', label: 'Created' },
    { value: 'updated_at', label: 'Updated' },
    { value: 'is_active', label: 'Active' },
];

export const FEED_SORT_OPTIONS = [
    { value: 'name', label: 'Name' },
    { value: 'last_scraped_at', label: 'Last scraped' },
    { value: 'created_at', label: 'Created' },
    { value: 'updated_at', label: 'Updated' },
    { value: 'is_active', label: 'Active' },
];

export const COLLECTION_SORT_OPTIONS = [
    { value: 'name', label: 'Name' },
    { value: 'created_at', label: 'Created' },
    { value: 'updated_at', label: 'Updated' },
];

export const ITEM_SORT_OPTIONS = [
    { value: 'source_updated_at', label: 'Updated' },
    { value: 'source_published_at', label: 'Published' },
    { value: 'scraped_at', label: 'Scraped' },
    { value: 'last_scraped_at', label: 'Last scraped' },
];
