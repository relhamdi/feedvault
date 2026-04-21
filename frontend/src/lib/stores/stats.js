import { writable } from 'svelte/store';
import { statsApi } from '../api/stats.js';

// { [feedId]: FeedStats }
export const feedStats = writable({});
// { [sourceId]: SourceStats }
export const sourceStats = writable({});

export async function refreshFeedStats(feedId) {
    try {
        const stats = await statsApi.feed(feedId);
        feedStats.update((s) => ({ ...s, [feedId]: stats }));
    } catch (e) {
        console.warn(`Failed to refresh stats for feed ${feedId}:`, e.message);
    }
}

export async function refreshSourceStats(sourceId) {
    try {
        const stats = await statsApi.source(sourceId);
        sourceStats.update((s) => ({ ...s, [sourceId]: stats }));
    } catch (e) {
        console.warn(`Failed to refresh stats for source ${sourceId}:`, e.message);
    }
}
