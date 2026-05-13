<script>
    import { collectionsMode, enterCollectionsMode } from '../../stores/navigation.js';
</script>

<button
    class="collection-item"
    class:active={$collectionsMode}
    on:click={enterCollectionsMode}
    title="Collections"
>
    <div class="collection-icon">
        <span>⊞</span>
    </div>
    <div class="source-info">
        <span class="source-name">Collections</span>
        <span class="source-type">smart feeds</span>
    </div>
</button>

<style>
    .collection-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        width: 100%;
        padding: 0.6rem 1rem;
        transition: background var(--transition);
        text-align: left;
        margin-bottom: 0.5rem;
    }

    .collection-item:hover {
        background: var(--bg-tertiary);
    }

    .collection-item.active {
        background: var(--bg-tertiary);
        box-shadow: inset 3px 0 0 var(--accent);
    }

    .collection-icon {
        width: 32px;
        height: 32px;
        border-radius: var(--radius);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        background: var(--bg-tertiary);
        border: 1px dashed var(--border);
        color: var(--text-muted);
        font-size: 1rem;
    }

    .collection-item.active .collection-icon {
        background: color-mix(in srgb, var(--accent) 12%, transparent);
        border-color: var(--accent);
        color: var(--accent);
    }

    .source-info {
        flex: 1;
        overflow: hidden;
    }

    .source-name {
        display: block;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
    }

    .source-type {
        display: block;
        font-size: 0.75rem;
        color: var(--text-muted);
    }
</style>
