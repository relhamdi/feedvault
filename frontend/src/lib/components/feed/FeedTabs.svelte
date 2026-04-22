<script>
    import { feedsApi } from '../../api/feeds.js';
    import { scrapeApi } from '../../api/scrape.js';
    import {
        selectedFeedId,
        selectedSourceId,
        triggerFeedRefresh,
    } from '../../stores/navigation.js';
    import { refreshFeedStats, refreshSourceStats } from '../../stores/stats.js';
    import FeedTab from './FeedTab.svelte';

    let feeds = [];
    let loading = true;
    let error = null;

    let scrapingFeedIds = new Set();

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
            alert(`Scrape failed: ${e.message}`);
        }
    }

    function pollJob(jobId, feedId) {
        const interval = setInterval(async () => {
            try {
                const job = await scrapeApi.getJob(jobId);
                if (job.status === 'done' || job.status === 'error') {
                    clearInterval(interval);
                    scrapingFeedIds.delete(feedId);
                    scrapingFeedIds = scrapingFeedIds;

                    if (job.status === 'error') alert(`Scrape error: ${job.error_message}`);
                    // Reload items if the completed feed is the selected one
                    if (job.status === 'done' && feedId === $selectedFeedId) {
                        triggerFeedRefresh();
                    }
                    refreshFeedStats(feedId);
                    refreshSourceStats($selectedSourceId);
                }
            } catch (_) {
                clearInterval(interval);
                scrapingFeedIds.delete(feedId);
                scrapingFeedIds = scrapingFeedIds;
            }
        }, 2000);
    }
</script>

{#if $selectedSourceId}
    <div class="feed-tabs-wrapper">
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
                    />
                {/each}
            {/if}
        </div>
        <button class="add-tab-btn" title="Add feed">+</button>
    </div>
{/if}

<style>
    .feed-tabs-wrapper {
        display: flex;
        align-items: center;
        border-bottom: 1px solid var(--border);
        background: var(--bg-secondary);
        min-height: 48px;
        gap: 0.25rem;
        padding-right: 0.5rem;
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
        width: 28px;
        height: 28px;
        border-radius: var(--radius);
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
