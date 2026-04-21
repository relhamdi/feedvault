<script>
    import { itemsApi } from '../../api/items.js';
    import { selectedFeedId, selectedSourceId } from '../../stores/navigation.js';
    import { refreshFeedStats, refreshSourceStats } from '../../stores/stats.js';
    import ItemModal from '../item/ItemModal.svelte';
    import ItemCard from './ItemCard.svelte';

    let items = [];
    let total = 0;
    let offset = 0;
    const limit = 50;
    let loading = false;
    let loadingMore = false;
    let error = null;

    let selectedItem = null;

    // Reload items whenever selected feed changes
    $: if ($selectedFeedId) resetAndLoad($selectedFeedId);

    async function resetAndLoad(feedId) {
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
                    <ItemCard {item} on:click={() => openItem(item)} />
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
            <ItemModal item={selectedItem} onClose={closeModal} onUpdate={handleItemUpdate} />
        {/if}
    </div>
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
