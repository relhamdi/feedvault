import { writable } from 'svelte/store';

export const selectedSourceId = writable(null);
export const selectedFeedId = writable(null);
export const selectedItemId = writable(null);
export const feedRefreshTrigger = writable(0);

export function triggerFeedRefresh() {
    feedRefreshTrigger.update((n) => n + 1);
}
