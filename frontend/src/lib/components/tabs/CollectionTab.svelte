<script>
    import { createEventDispatcher, onMount } from 'svelte';
    import { collectionStats, refreshCollectionStats } from '../../stores/stats.js';

    export let collection;
    export let active = false;

    const dispatch = createEventDispatcher();

    onMount(() => refreshCollectionStats(collection.id));

    $: stats = $collectionStats[collection.id] ?? null;
</script>

<div
    class="collection-tab-wrapper"
    role="group"
    on:contextmenu={(e) => {
        e.preventDefault();
        dispatch('contextmenu', e);
    }}
>
    <button
        class="collection-tab"
        class:active
        on:click={() => dispatch('select')}
        title={collection.name}
    >
        {#if collection.color}
            <span class="collection-dot" style="background:{collection.color}"></span>
        {/if}

        <span class="collection-name">{collection.name}</span>

        {#if stats !== null}
            <span class="unread-badge" class:zero={stats.unread === 0}>
                {stats.unread}
            </span>
        {:else}
            <span class="unread-badge zero">–</span>
        {/if}
    </button>
</div>

<style>
    .collection-tab-wrapper {
        display: flex;
        align-items: center;
        flex-shrink: 0;
        border-radius: var(--radius);
    }

    .collection-tab {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.375rem 0.75rem;
        border-radius: var(--radius);
        font-size: 0.875rem;
        white-space: nowrap;
        color: var(--text-secondary);
        transition:
            background var(--transition),
            color var(--transition);
    }

    .collection-tab:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .collection-tab.active {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-weight: 500;
        box-shadow: inset 0 -2px 0 var(--accent);
    }

    .collection-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .collection-name {
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .unread-badge {
        background: var(--accent);
        color: white;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 0.1rem 0.35rem;
        border-radius: 99px;
        min-width: 16px;
        text-align: center;
        transition: background var(--transition);
    }

    .unread-badge.zero {
        background: var(--bg-tertiary);
        color: var(--text-muted);
    }
</style>
