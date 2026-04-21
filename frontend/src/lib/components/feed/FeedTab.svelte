<script>
    import { createEventDispatcher, onMount } from 'svelte';
    import { feedStats, refreshFeedStats } from '../../stores/stats.js';

    export let feed;
    export let active = false;

    const dispatch = createEventDispatcher();

    onMount(() => refreshFeedStats(feed.id));

    $: stats = $feedStats[feed.id] ?? null;
</script>

<button class="feed-tab" class:active on:click={() => dispatch('select')} title={feed.name}>
    {#if feed.icon_path}
        <img class="feed-icon" src={feed.icon_path} alt={feed.name} />
    {/if}

    <span class="feed-name">{feed.name}</span>

    {#if stats !== null}
        <span class="unread-badge" class:zero={stats.unread === 0}>
            {stats.unread}
        </span>
    {:else}
        <span class="unread-badge zero">–</span>
    {/if}
</button>

<style>
    .feed-tab {
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
        flex-shrink: 0;
    }

    .feed-tab:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .feed-tab.active {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-weight: 500;
        box-shadow: inset 0 -2px 0 var(--accent);
    }

    .feed-icon {
        width: 16px;
        height: 16px;
        border-radius: 3px;
        object-fit: cover;
    }

    .feed-name {
        max-width: none;
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
