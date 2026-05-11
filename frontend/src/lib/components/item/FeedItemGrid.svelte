<script>
    import { onDestroy } from 'svelte';
    import { itemsApi } from '../../api/items.js';
    import { sourcesApi } from '../../api/sources.js';
    import { itemFilters, resetFilters } from '../../stores/filters.js';
    import {
        feedRefreshTrigger,
        selectedFeedId,
        selectedSourceId,
    } from '../../stores/navigation.js';
    import { itemSort } from '../../stores/sorting.js';
    import { refreshFeedStats, refreshSourceStats } from '../../stores/stats.js';
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

    const MENU_ID = 'feed-itemgrid';

    let searchDebounce;
    let items = [];
    let total = 0;
    let offset = 0;
    let loading = false;
    let loadingMore = false;
    let error = null;

    let selectedItem = null;
    let contextMenu = null;
    let currentParamsSchema = {};
    let refreshingItemIds = new Set();
    const cleanups = [];

    $: if ($selectedFeedId) {
        loadParamsSchema();
        resetFilters();
        resetAndLoad();
    }
    $: if ($feedRefreshTrigger) resetAndLoad();
    $: if ($activeContextMenuId !== MENU_ID) contextMenu = null;
    $: if ($itemFilters || $itemSort) {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(
            resetAndLoad,
            $itemFilters.search || $itemFilters.tags ? 300 : 0
        );
    }

    $: canRefresh = 'external_ids' in currentParamsSchema;

    onDestroy(() => cleanups.forEach((fn) => fn()));

    async function loadParamsSchema() {
        try {
            const source = await sourcesApi.get($selectedSourceId);
            currentParamsSchema = await sourcesApi.paramsSchema(source.slug);
        } catch (e) {
            console.warn(`Failed to load params schema for source ${source.slug}:`, e.message);
            currentParamsSchema = {};
        }
    }

    async function resetAndLoad() {
        if (!$selectedFeedId) return;
        offset = 0;
        items = [];
        total = 0;
        await loadItems();
    }

    async function loadItems() {
        if (!$selectedFeedId || loading || loadingMore) return;
        offset === 0 ? (loading = true) : (loadingMore = true);
        error = null;
        try {
            const response = await itemsApi.list(
                $selectedFeedId,
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
        refreshFeedStats($selectedFeedId);
        refreshSourceStats($selectedSourceId);
    }

    function handleCardContextMenu(e, item) {
        activeContextMenuId.set(MENU_ID);
        contextMenu = { x: e.clientX, y: e.clientY, item };
    }

    async function toggleRead(item) {
        await doToggleRead(item, items, (updated) => {
            items = items.map((i) => (i.id === item.id ? updated : i));
            refreshFeedStats($selectedFeedId);
            refreshSourceStats($selectedSourceId);
        });
    }

    async function toggleFavorite(item) {
        await doToggleFavorite(item, (updated) => {
            items = items.map((i) => (i.id === item.id ? updated : i));
        });
    }

    async function refreshItem(item) {
        if (refreshingItemIds.has(item.id)) return;
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
</script>

{#if $selectedFeedId}
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
                        on:click={() => (selectedItem = item)}
                        on:contextmenu={(e) => handleCardContextMenu(e.detail, item)}
                    />
                {/each}
            </div>
        {/if}

        {#if loadingMore}
            <p class="grid-status">Loading more...</p>
        {:else if items.length >= total && total > 0}
            <p class="grid-status">{total} item(s)</p>
        {/if}

        {#if selectedItem}
            <ItemModal
                item={selectedItem}
                feedId={$selectedFeedId}
                paramsSchema={currentParamsSchema}
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
            canRefresh,
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
