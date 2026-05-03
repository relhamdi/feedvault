import { writable } from 'svelte/store';

export const selectedSourceId = writable(null);
export const selectedFeedId = writable(null);
export const selectedItemId = writable(null);
export const selectedCollectionId = writable(null);

export const sourceRefreshTrigger = writable(0);
export const feedRefreshTrigger = writable(0);
export const collectionRefreshTrigger = writable(0);

export const collectionsMode = writable(false);

export function triggerSourceRefresh() {
    sourceRefreshTrigger.update((n) => n + 1);
}

export function triggerFeedRefresh() {
    feedRefreshTrigger.update((n) => n + 1);
}

export function triggerCollectionRefresh() {
    collectionRefreshTrigger.update((n) => n + 1);
}

/**
 * Switch to source mode
 */
export function selectSource(id) {
    selectedSourceId.set(id);
    selectedFeedId.set(null);
    selectedCollectionId.set(null);
    collectionsMode.set(false);
}

/**
 * Switch to collections mode
 */
export function selectCollection(id) {
    selectedCollectionId.set(id);
    selectedSourceId.set(null);
    selectedFeedId.set(null);
    collectionsMode.set(true);
}

// Alias for clarity
export function enterCollectionsMode() {
    selectCollection(null);
}
