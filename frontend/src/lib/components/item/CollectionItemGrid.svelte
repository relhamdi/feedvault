<script>
    import { onDestroy, onMount } from 'svelte';
    import { collectionsApi } from '../../api/collections.js';
    import { feedsApi } from '../../api/feeds.js';
    import { sourcesApi } from '../../api/sources.js';
    import { itemFilters, resetFilters } from '../../stores/filters.js';
    import { collectionRefreshTrigger, selectedCollectionId } from '../../stores/navigation.js';
    import { itemSort } from '../../stores/sorting.js';
    import {
        refreshCollectionStats,
        refreshFeedStats,
        refreshSourceStats,
    } from '../../stores/stats.js';
    import { toastError } from '../../stores/toast.js';
    import { activeContextMenuId, gridSize } from '../../stores/ui.js';
    import {
        buildContextMenuItems,
        buildItemParams,
        refreshItem as doRefreshItem,
        toggleFavorite as doToggleFavorite,
        toggleRead as doToggleRead,
    } from '../../utils/itemGridState.js';
    import ItemCard from '../item/ItemCard.svelte';
    import ItemModal from '../modals/ItemModal.svelte';
    import ContextMenu from '../ui/ContextMenu.svelte';

    const MENU_ID = 'collection-itemgrid';

    let searchDebounce;
    let items = [];
    let total = 0;
    let offset = 0;
    let loading = false;
    let loadingMore = false;
    let error = null;

    let selectedItem = null;
    let contextMenu = null;
    let selectedItemSchema = {};

    let feedSourceMap = {};
    let paramsSchemaCache = {};
    let refreshingItemIds = new Set();
    const cleanups = [];

    $: if ($selectedCollectionId) {
        resetFilters();
        resetAndLoad();
    }
    $: if ($collectionRefreshTrigger) resetAndLoad();
    $: if ($activeContextMenuId !== MENU_ID) contextMenu = null;
    $: if ($itemFilters || $itemSort) {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(
            resetAndLoad,
            $itemFilters.search || $itemFilters.tags ? 300 : 0
        );
    }

    onMount(buildFeedSourceMap);
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

    async function getParamsSchema(item) {
        const slug = feedSourceMap[item.feed_id]?.slug;
        if (!slug) return {};
        if (paramsSchemaCache[slug]) return paramsSchemaCache[slug];
        try {
            paramsSchemaCache[slug] = await sourcesApi.paramsSchema(slug);
        } catch (e) {
            console.warn(`Failed to load param schema for feed ${item.feed_id}:`, e.message);
            paramsSchemaCache[slug] = {};
        }
        return paramsSchemaCache[slug];
    }

    async function resetAndLoad() {
        if (!$selectedCollectionId) return;
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
            const response = await collectionsApi.items(
                $selectedCollectionId,
                buildItemParams($itemFilters, $itemSort, offset)
            );
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

    function handleItemUpdate(updatedItem) {
        items = items.map((i) => (i.id === updatedItem.id ? updatedItem : i));
        selectedItem = updatedItem;
        refreshCollectionStats($selectedCollectionId);
        refreshFeedStats(updatedItem.feed_id);
        const sourceId = feedSourceMap[updatedItem.feed_id]?.sourceId;
        if (sourceId) refreshSourceStats(sourceId);
    }

    async function handleCardContextMenu(e, item) {
        activeContextMenuId.set(MENU_ID);
        const schema = await getParamsSchema(item);
        const canRefresh = 'external_ids' in schema;
        contextMenu = { x: e.clientX, y: e.clientY, item, canRefresh };
    }

    async function toggleRead(item) {
        await doToggleRead(item, items, (updated) => {
            items = items.map((i) => (i.id === item.id ? updated : i));
            refreshCollectionStats($selectedCollectionId);
            refreshFeedStats(item.feed_id);
            const sourceId = feedSourceMap[item.feed_id]?.sourceId;
            if (sourceId) refreshSourceStats(sourceId);
        });
    }

    async function toggleFavorite(item) {
        await doToggleFavorite(item, (updated) => {
            items = items.map((i) => (i.id === item.id ? updated : i));
        });
    }

    async function refreshItem(item) {
        if (refreshingItemIds.has(item.id)) return;
        const schema = await getParamsSchema(item);
        if (!('external_ids' in schema)) {
            toastError('This source does not support per-item refresh.');
            return;
        }
        refreshingItemIds.add(item.id);
        refreshingItemIds = refreshingItemIds;

        const cleanup = await doRefreshItem(item, {
            onDone: (updated) => {
                refreshingItemIds.delete(item.id);
                refreshingItemIds = refreshingItemIds;
                items = items.map((i) => (i.id === updated.id ? updated : i));
            },
            onError: () => {
                refreshingItemIds.delete(item.id);
                refreshingItemIds = refreshingItemIds;
            },
        });
        if (cleanup) cleanups.push(cleanup);
    }

    async function openItem(item) {
        selectedItem = item;
        selectedItemSchema = await getParamsSchema(item);
    }
</script>

{#if $selectedCollectionId}
    <div class="item-grid-wrapper" on:scroll={handleScroll}>
        {#if loading}
            <p class="grid-status">Loading...</p>
        {:else if error}
            <p class="grid-status error">{error}</p>
        {:else if items.length === 0}
            <p class="grid-status">No items here.</p>
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
            <p class="grid-status muted">{total} item(s)</p>
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
        items={buildContextMenuItems({
            item: contextMenu.item,
            canRefresh: contextMenu.canRefresh ?? false,
            onToggleRead: toggleRead,
            onToggleFavorite: toggleFavorite,
            onRefresh: refreshItem,
        })}
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
