import { writable } from 'svelte/store';

function sessionFilters() {
    return writable({
        search: '',
        tags: '',
        is_read: null,
        is_favorite: null,
        is_nsfw: null,
        is_public: null,
    });
}

// Shared instance for collections and feeds
export const itemFilters = sessionFilters();

export const DEFAULT_FILTERS = {
    search: '',
    tags: '',
    is_read: null,
    is_favorite: null,
    is_nsfw: null,
    is_public: null,
};

export function resetFilters() {
    itemFilters.set({ ...DEFAULT_FILTERS });
}
