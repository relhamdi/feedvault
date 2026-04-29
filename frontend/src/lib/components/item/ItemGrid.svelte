<script>
    import { onDestroy } from 'svelte';
    import { itemsApi } from '../../api/items.js';
    import { scrapeApi } from '../../api/scrape.js';
    import { sourcesApi } from '../../api/sources.js';
    import {
        feedRefreshTrigger,
        selectedFeedId,
        selectedSourceId,
    } from '../../stores/navigation.js';
    import { pollJob } from '../../stores/scraping.js';
    import { refreshFeedStats, refreshSourceStats } from '../../stores/stats.js';
    import { toastError, toastInfo, toastSuccess } from '../../stores/toast.js';
    import ItemModal from '../modals/ItemModal.svelte';
    import ContextMenu from '../ui/ContextMenu.svelte';
    import ItemCard from './ItemCard.svelte';

    let items = [];
    let total = 0;
    let offset = 0;
    const limit = 50;
    let loading = false;
    let loadingMore = false;
    let error = null;

    let selectedItem = null;
    let contextMenu = null;

    // Loaded schema for item modal
    let currentParamsSchema = {};

    // Scraping
    let refreshingItemIds = new Set();
    const cleanups = [];

    $: if ($selectedFeedId) loadParamsSchema();

    // Reload items whenever selected feed changes
    $: if ($selectedFeedId || $feedRefreshTrigger) resetAndLoad($selectedFeedId);

    onDestroy(() => cleanups.forEach((fn) => fn()));

    async function loadParamsSchema() {
        try {
            // Get source slug from current source
            const source = await sourcesApi.get($selectedSourceId);
            currentParamsSchema = await sourcesApi.paramsSchema(source.slug);
        } catch (e) {
            console.warn(`Failed to load paramsSchema for ${selectedSourceId}:`, e.message);
            currentParamsSchema = {};
        }
    }

    async function resetAndLoad(feedId) {
        if (!feedId) return;
        offset = 0;
        items = [];
        total = 0;
        await loadItems(feedId);
    }

    async function loadItems(feedId) {
        if (loading || loadingMore) return;
        offset === 0 ? (loading = true) : (loadingMore = true);

        error = null;
        try {
            const response = await itemsApi.list(feedId, { limit, offset });
            items = offset === 0 ? response.items : [...items, ...response.items];
            total = response.total;
            offset += response.items.length;
        } catch (e) {
            error = e.message;
            toastError('Failed to load items');
        } finally {
            loading = false;
            loadingMore = false;
        }
    }

    function handleScroll(e) {
        const el = e.target;
        const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 200;
        if (nearBottom && items.length < total && !loadingMore) {
            loadItems($selectedFeedId);
        }
    }

    function openItem(item) {
        selectedItem = item;
    }

    function closeModal() {
        selectedItem = null;
    }

    function handleItemUpdate(updatedItem) {
        items = items.map((i) => (i.id === updatedItem.id ? updatedItem : i));
        selectedItem = updatedItem;
        refreshFeedStats($selectedFeedId);
        refreshSourceStats($selectedSourceId);
    }

    function handleCardContextMenu(e, item) {
        e.preventDefault();
        contextMenu = { x: e.clientX, y: e.clientY, item };
    }

    async function toggleRead(item) {
        try {
            const updated = { ...item, is_read: !item.is_read };
            await itemsApi.update(item.id, { is_read: updated.is_read });
            items = items.map((i) => (i.id === item.id ? updated : i));
            refreshFeedStats($selectedFeedId);
            refreshSourceStats($selectedSourceId);
        } catch (e) {
            console.error('Failed to update item:', e.message);
            toastError(`Failed to update item: ${e.message}`);
        }
    }

    async function toggleFavorite(item) {
        try {
            const updated = { ...item, is_favorite: !item.is_favorite };
            await itemsApi.update(item.id, { is_favorite: updated.is_favorite });
            items = items.map((i) => (i.id === item.id ? updated : i));
        } catch (e) {
            console.error('Failed to update item:', e.message);
            toastError(`Failed to update item: ${e.message}`);
        }
    }

    async function refreshItem(item) {
        if (refreshingItemIds.has(item.id)) return;
        refreshingItemIds.add(item.id);
        refreshingItemIds = refreshingItemIds;
        try {
            const job = await scrapeApi.scrape({
                feed_id: $selectedFeedId,
                mode: 'FULL',
                external_ids: [item.external_id],
            });
            toastInfo(`Refreshing item "${item.title}"...`);
            const cleanup = pollJob(job.id, {
                onDone: async () => {
                    refreshingItemIds.delete(item.id);
                    refreshingItemIds = refreshingItemIds;
                    toastSuccess(`"${item.title}" refreshed`);
                    const updated = await itemsApi.get(item.id);
                    items = items.map((i) => (i.id === updated.id ? updated : i));
                },
                onError: (msg) => {
                    refreshingItemIds.delete(item.id);
                    refreshingItemIds = refreshingItemIds;
                    toastError(`Refresh error: ${msg}`);
                },
            });
            cleanups.push(cleanup);
        } catch (e) {
            refreshingItemIds.delete(item.id);
            refreshingItemIds = refreshingItemIds;
            console.error('Refresh failed:', e.message);
            toastError(`Refresh failed: ${e.message}`);
        }
    }
</script>

{#if $selectedFeedId}
    <div class="item-grid-wrapper" on:scroll={handleScroll}>
        {#if loading}
            <p class="grid-status">Loading...</p>
        {:else if error}
            <p class="grid-status error">{error}</p>
        {:else if items.length === 0}
            <p class="grid-status">No items yet.</p>
        {:else}
            <div class="item-grid">
                {#each items as item (item.id)}
                    <ItemCard
                        {item}
                        on:click={() => openItem(item)}
                        on:contextmenu={(e) => handleCardContextMenu(e.detail, item)}
                    />
                {/each}
            </div>
        {/if}

        {#if loadingMore}
            <p class="grid-status">Loading more...</p>
        {:else if items.length >= total && total > 0}
            <p class="grid-status muted">
                {total} items · {Math.ceil(offset / limit)} page
            </p>
        {/if}

        {#if selectedItem}
            <ItemModal
                item={selectedItem}
                feedId={$selectedFeedId}
                paramsSchema={currentParamsSchema}
                onClose={closeModal}
                onUpdate={handleItemUpdate}
            />
        {/if}
    </div>
{/if}

{#if contextMenu}
    <ContextMenu
        x={contextMenu.x}
        y={contextMenu.y}
        items={[
            {
                label: contextMenu.item.is_read ? 'Mark as unread' : 'Mark as read',
                icon: contextMenu.item.is_read ? '○' : '●',
                action: () => toggleRead(contextMenu.item),
            },
            {
                label: contextMenu.item.is_favorite ? 'Remove from favorites' : 'Add to favorites',
                icon: contextMenu.item.is_favorite ? '♥' : '♡',
                action: () => toggleFavorite(contextMenu.item),
            },
            ...(currentParamsSchema && 'external_ids' in currentParamsSchema
                ? [
                      { separator: true },
                      {
                          label: 'Refresh item',
                          icon: '⟳',
                          action: () => refreshItem(contextMenu.item),
                      },
                  ]
                : []),
        ]}
        onClose={() => (contextMenu = null)}
    />
{/if}

<style>
    .item-grid-wrapper {
        height: 100%;
        overflow-y: auto;
        padding: 1rem;
    }

    .grid-status {
        text-align: center;
        color: var(--text-muted);
        font-size: 0.875rem;
        padding: 1rem 0;
    }

    .grid-status.error {
        color: var(--danger);
    }

    .item-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1rem;
    }
</style>
