<script>
    import { onDestroy, onMount } from 'svelte';
    import { collectionsApi } from '../../api/collections.js';
    import { feedsApi } from '../../api/feeds.js';
    import { itemsApi } from '../../api/items.js';
    import { scrapeApi } from '../../api/scrape.js';
    import { sourcesApi } from '../../api/sources.js';
    import { collectionRefreshTrigger, selectedCollectionId } from '../../stores/navigation.js';
    import { pollJob } from '../../stores/scraping.js';
    import {
        refreshCollectionStats,
        refreshFeedStats,
        refreshSourceStats,
    } from '../../stores/stats.js';
    import { toastError, toastInfo, toastSuccess } from '../../stores/toast.js';
    import { gridSize } from '../../stores/ui.js';
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

    // Map feedId -> { name, color, slug, sourceId }
    let feedSourceMap = {};
    // sourceSlug -> paramsSchema (cached)
    let paramsSchemaCache = {};
    // sourceSlug -> paramsSchema for selectedItem (for ItemModal)
    let selectedItemSchema = {};

    // Scraping
    let refreshingItemIds = new Set();
    const cleanups = [];

    $: if ($selectedCollectionId) resetAndLoad();
    $: if ($collectionRefreshTrigger && $selectedCollectionId) resetAndLoad();

    onMount(async () => {
        await buildFeedSourceMap();
    });

    onDestroy(() => cleanups.forEach((fn) => fn()));

    async function buildFeedSourceMap() {
        try {
            const [sourcesRes, feedsRes] = await Promise.all([
                sourcesApi.list({ limit: 200 }),
                feedsApi.listAll({ limit: 200 }),
            ]);
            const sourceById = Object.fromEntries(sourcesRes.items.map((s) => [s.id, s]));
            feedSourceMap = Object.fromEntries(
                feedsRes.items.map((f) => [
                    f.id,
                    {
                        name: sourceById[f.source_id]?.name ?? '?',
                        color: sourceById[f.source_id]?.color ?? null,
                        slug: sourceById[f.source_id]?.slug ?? '',
                        sourceId: f.source_id,
                    },
                ])
            );
        } catch (e) {
            console.warn('Failed to build feed source map:', e.message);
            feedSourceMap = {};
        }
    }

    async function resetAndLoad() {
        offset = 0;
        items = [];
        total = 0;
        await loadItems();
    }

    async function loadItems() {
        if (!$selectedCollectionId || loading || loadingMore) return;
        offset === 0 ? (loading = true) : (loadingMore = true);

        error = null;
        try {
            const response = await collectionsApi.items($selectedCollectionId, { limit, offset });
            items = offset === 0 ? response.items : [...items, ...response.items];
            total = response.total;
            offset += response.items.length;
        } catch (e) {
            error = e.message;
            toastError('Failed to load collection items');
        } finally {
            loading = false;
            loadingMore = false;
        }
    }

    function handleScroll(e) {
        const el = e.target;
        const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 200;
        if (nearBottom && items.length < total && !loadingMore) {
            loadItems();
        }
    }

    async function getParamsSchema(item) {
        const sourceInfo = feedSourceMap[item.feed_id];
        if (!sourceInfo) return {};
        const slug = sourceInfo.slug;
        if (paramsSchemaCache[slug]) return paramsSchemaCache[slug];
        try {
            paramsSchemaCache[slug] = await sourcesApi.paramsSchema(slug);
        } catch (e) {
            console.warn('Failed to fetch paramsSchema:', e.message);
            paramsSchemaCache[slug] = {};
        }
        return paramsSchemaCache[slug];
    }

    async function openItem(item) {
        selectedItem = item;
        selectedItemSchema = await getParamsSchema(item);
    }

    function handleItemUpdate(updatedItem) {
        items = items.map((i) => (i.id === updatedItem.id ? updatedItem : i));
        selectedItem = updatedItem;
        refreshCollectionStats($selectedCollectionId);
        refreshFeedStats(updatedItem.feed_id);
        const sourceId = feedSourceMap[updatedItem.feed_id]?.sourceId;
        if (sourceId) refreshSourceStats(sourceId);
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
            refreshCollectionStats($selectedCollectionId);
            refreshFeedStats(item.feed_id);
            const sourceId = feedSourceMap[item.feed_id]?.sourceId;
            if (sourceId) refreshSourceStats(sourceId);
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
        const schema = await getParamsSchema(item);
        if (!schema || !('external_ids' in schema)) {
            toastError('This source does not support per-item refresh.');
            return;
        }
        refreshingItemIds.add(item.id);
        refreshingItemIds = refreshingItemIds;

        try {
            const job = await scrapeApi.scrape({
                feed_id: item.feed_id,
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

{#if $selectedCollectionId}
    <div class="item-grid-wrapper" on:scroll={handleScroll}>
        {#if loading}
            <p class="grid-status">Loading...</p>
        {:else if error}
            <p class="grid-status error">{error}</p>
        {:else if items.length === 0}
            <p class="grid-status">No items in this collection.</p>
        {:else}
            <div
                class="item-grid"
                style="grid-template-columns: repeat(auto-fill, minmax({$gridSize}px, 1fr))"
            >
                {#each items as item (item.id)}
                    <ItemCard
                        {item}
                        source={feedSourceMap[item.feed_id] ?? null}
                        on:click={() => openItem(item)}
                        on:contextmenu={(e) => handleCardContextMenu(e.detail, item)}
                    />
                {/each}
            </div>
        {/if}

        {#if loadingMore}
            <p class="grid-status">Loading more...</p>
        {:else if items.length >= total && total > 0}
            <p class="grid-status muted">{total} items</p>
        {/if}

        {#if selectedItem}
            <ItemModal
                item={selectedItem}
                feedId={selectedItem.feed_id}
                paramsSchema={selectedItemSchema}
                onClose={() => (selectedItem = null)}
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
            { separator: true },
            { label: 'Refresh item', icon: '⟳', action: () => refreshItem(contextMenu.item) },
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
        gap: 1rem;
    }
</style>
