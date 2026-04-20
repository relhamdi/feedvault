<script>
    import { createEventDispatcher } from 'svelte';

    export let source;
    export let active = false;

    const dispatch = createEventDispatcher();
</script>

<button class="source-item" class:active on:click={() => dispatch('select')} title={source.name}>
    <div class="source-icon" style="background: {source.color || 'var(--bg-tertiary)'}">
        {#if source.icon_path}
            <img src={source.icon_path} alt={source.name} />
        {:else}
            <span>{source.name.charAt(0).toUpperCase()}</span>
        {/if}
    </div>

    <div class="source-info">
        <span class="source-name">{source.name}</span>
        <span class="source-type">{source.source_type}</span>
    </div>

    <div class="source-meta">
        {#if !source.is_active}
            <span class="badge inactive" title="Inactive">●</span>
        {/if}
        <!-- Unread count badge — wired later -->
        <span class="unread-badge">0</span>
    </div>
</button>

<style>
    .source-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        width: 100%;
        padding: 0.6rem 1rem;
        border-radius: 0;
        transition: background var(--transition);
        text-align: left;
    }

    .source-item:hover {
        background: var(--bg-tertiary);
    }

    .source-item.active {
        background: var(--bg-tertiary);
        box-shadow: inset 3px 0 0 var(--accent);
    }

    .source-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-weight: 600;
        font-size: 0.875rem;
        color: white;
        overflow: hidden;
    }

    .source-icon img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .source-info {
        flex: 1;
        overflow: hidden;
    }

    .source-name {
        display: block;
        font-size: 0.875rem;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--text-primary);
    }

    .source-type {
        display: block;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: lowercase;
    }

    .source-meta {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-shrink: 0;
    }

    .badge.inactive {
        color: var(--text-muted);
        font-size: 0.6rem;
    }

    .unread-badge {
        background: var(--accent);
        color: white;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.1rem 0.4rem;
        border-radius: 99px;
        min-width: 18px;
        text-align: center;
    }
</style>
