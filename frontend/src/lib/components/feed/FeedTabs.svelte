<script>
    import { onDestroy } from 'svelte';
    import { feedsApi } from '../../api/feeds.js';
    import { scrapeApi } from '../../api/scrape.js';
    import {
        selectedFeedId,
        selectedSourceId,
        triggerFeedRefresh,
    } from '../../stores/navigation.js';
    import { refreshFeedStats, refreshSourceStats } from '../../stores/stats.js';
    import { toastError, toastSuccess } from '../../stores/toast.js';
    import ConfirmModal from '../ui/ConfirmModal.svelte';
    import ContextMenu from '../ui/ContextMenu.svelte';
    import FeedModal from '../ui/FeedModal.svelte';
    import FeedTab from './FeedTab.svelte';

    let feeds = [];
    let loading = true;
    let error = null;

    // Modals
    let showFeedModal = false;
    let editingFeed = null;

    // Confirm delete
    let showConfirm = false;
    let deletingFeed = null;

    // Context menu
    let contextMenu = null;

    // Scraping
    let scrapingFeedIds = new Set();
    let pollingIntervals = {};

    // Reload feeds whenever selected source changes
    $: if ($selectedSourceId) loadFeeds($selectedSourceId);

    async function loadFeeds(sourceId) {
        loading = true;
        error = null;
        feeds = [];
        try {
            feeds = (await feedsApi.list(sourceId)).items;
            // Auto-select first feed if none selected
            if (feeds.length > 0 && !$selectedFeedId) {
                selectedFeedId.set(feeds[0].id);
            }
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    function openCreate() {
        editingFeed = null;
        showFeedModal = true;
        contextMenu = null;
    }

    function openEdit(feed) {
        editingFeed = feed;
        showFeedModal = true;
        contextMenu = null;
    }

    function openDelete(feed) {
        deletingFeed = feed;
        showConfirm = true;
        contextMenu = null;
    }

    async function handleDelete() {
        if (!deletingFeed) return;
        const toDelete = deletingFeed;
        try {
            await feedsApi.delete(toDelete.id);
            feeds = feeds.filter((f) => f.id !== toDelete.id);
            if ($selectedFeedId === toDelete.id) {
                selectedFeedId.set(feeds[0]?.id ?? null);
            }
            refreshSourceStats($selectedSourceId);
        } catch (e) {
            console.error('Delete failed:', e.message);
        }
    }

    function handleSaved(saved) {
        const idx = feeds.findIndex((f) => f.id === saved.id);
        if (idx >= 0) {
            feeds[idx] = saved;
            feeds = feeds;
        } else {
            feeds = [...feeds, saved];
            selectedFeedId.set(saved.id);
        }
    }

    function handleContextMenu(e, feed) {
        contextMenu = { x: e.detail.clientX, y: e.detail.clientY, feed };
    }

    async function startScrape(feedId) {
        if (scrapingFeedIds.has(feedId)) return;
        scrapingFeedIds.add(feedId);
        scrapingFeedIds = scrapingFeedIds; // trigger Svelte reactivity
        try {
            const job = await scrapeApi.scrape({ feed_id: feedId, mode: 'INCREMENTAL' });
            pollJob(job.id, feedId);
        } catch (e) {
            scrapingFeedIds.delete(feedId);
            scrapingFeedIds = scrapingFeedIds;
            toastError(`Scrape failed: ${e.message}`);
        }
    }

    function pollJob(jobId, feedId) {
        pollingIntervals[feedId] = setInterval(async () => {
            try {
                const job = await scrapeApi.getJob(jobId);
                if (job.status === 'done' || job.status === 'error') {
                    clearInterval(pollingIntervals[feedId]);
                    delete pollingIntervals[feedId];
                    scrapingFeedIds.delete(feedId);
                    scrapingFeedIds = scrapingFeedIds;

                    if (job.status === 'error') {
                        console.error('Scrape error:', job.error_message);
                        toastError(`Scrape error: ${job.error_message}`);
                    }
                    // Reload items if the completed feed is the selected one
                    if (job.status === 'done' && feedId === $selectedFeedId) {
                        toastSuccess(`Scrape complete — ${job.items_upserted} items`);
                        triggerFeedRefresh();
                    }
                    refreshFeedStats(feedId);
                    refreshSourceStats($selectedSourceId);
                }
            } catch (_) {
                clearInterval(pollingIntervals[feedId]);
                delete pollingIntervals[feedId];
                scrapingFeedIds.delete(feedId);
                scrapingFeedIds = scrapingFeedIds;
            }
        }, 2000);
    }

    onDestroy(() => {
        Object.values(pollingIntervals).forEach(clearInterval);
    });
</script>

{#if $selectedSourceId}
    <div class="feed-tabs-wrapper">
        <button class="add-tab-btn" title="Add feed" on:click={openCreate}>+</button>
        <div class="feed-tabs">
            {#if loading}
                <span class="tabs-status">Loading...</span>
            {:else if error}
                <span class="tabs-status error">{error}</span>
            {:else if feeds.length === 0}
                <span class="tabs-status">No feeds yet.</span>
            {:else}
                {#each feeds as feed (feed.id)}
                    <FeedTab
                        {feed}
                        active={$selectedFeedId === feed.id}
                        scraping={scrapingFeedIds.has(feed.id)}
                        on:select={() => selectedFeedId.set(feed.id)}
                        on:scrape={() => startScrape(feed.id)}
                        on:contextmenu={(e) => handleContextMenu(e, feed)}
                    />
                {/each}
            {/if}
        </div>
    </div>
{/if}

<!-- Context menu -->
{#if contextMenu}
    <ContextMenu
        x={contextMenu.x}
        y={contextMenu.y}
        items={[
            { label: 'Edit', icon: '✎', action: () => openEdit(contextMenu.feed) },
            { label: 'Scrape', icon: '⟳', action: () => startScrape(contextMenu.feed.id) },
            { separator: true },
            {
                label: 'Delete',
                icon: '✕',
                danger: true,
                action: () => openDelete(contextMenu.feed),
            },
        ]}
        onClose={() => (contextMenu = null)}
    />
{/if}

<!-- Feed modal -->
{#if showFeedModal}
    <FeedModal
        feed={editingFeed}
        sourceId={$selectedSourceId}
        onClose={() => (showFeedModal = false)}
        onSaved={handleSaved}
    />
{/if}

<!-- Confirm delete -->
{#if showConfirm && deletingFeed}
    <ConfirmModal
        title="Delete feed"
        message="Delete «{deletingFeed.name}»? All items will be permanently deleted."
        onConfirm={handleDelete}
        onClose={() => {
            showConfirm = false;
            deletingFeed = null;
        }}
    />
{/if}

<style>
    .feed-tabs-wrapper {
        display: flex;
        align-items: center;
        border-bottom: 1px solid var(--border);
        background: var(--bg-secondary);
        min-height: 48px;
    }

    .feed-tabs {
        display: flex;
        align-items: center;
        overflow-x: auto;
        flex: 1;
        gap: 0.25rem;
        padding: 0.375rem 0.5rem;
        scrollbar-width: none; /* Firefox */
    }

    .feed-tabs::-webkit-scrollbar {
        display: none; /* Chrome/Safari */
    }

    .tabs-status {
        padding: 0 0.5rem;
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .tabs-status.error {
        color: var(--danger);
    }

    .add-tab-btn {
        flex-shrink: 0;
        width: 48px;
        height: 48px;
        border-radius: 0;
        border-right: 1px solid var(--border);
        padding-bottom: 5px;
        color: var(--text-muted);
        font-size: 1.25rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition:
            background var(--transition),
            color var(--transition);
    }

    .add-tab-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
</style>
