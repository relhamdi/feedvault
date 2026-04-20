<script>
    import { itemsApi } from '../../api/items.js';
    import { selectedFeedId } from '../../stores/navigation.js';
    import ItemCard from './ItemCard.svelte';

    let items = [];
    let loading = true;
    let error = null;

    // Reload items whenever selected feed changes
    $: if ($selectedFeedId) loadItems($selectedFeedId);

    async function loadItems(feedId) {
        loading = true;
        error = null;
        items = [];
        try {
            items = await itemsApi.list(feedId);
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }
</script>

{#if $selectedFeedId}
    <div class="item-grid-wrapper">
        {#if loading}
            <p class="grid-status">Loading...</p>
        {:else if error}
            <p class="grid-status error">{error}</p>
        {:else if items.length === 0}
            <p class="grid-status">No items yet.</p>
        {:else}
            <div class="item-grid">
                {#each items as item (item.id)}
                    <ItemCard {item} />
                {/each}
            </div>
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
