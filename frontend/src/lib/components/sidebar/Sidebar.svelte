<script>
    import { onMount } from 'svelte';
    import { sourcesApi } from '../../api/sources.js';
    import { selectedFeedId, selectedSourceId } from '../../stores/navigation.js';
    import SourceItem from './SourceItem.svelte';

    let sources = [];
    let loading = true;
    let error = null;

    onMount(async () => {
        try {
            sources = await sourcesApi.list();
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    });

    function selectSource(id) {
        selectedSourceId.set(id);
        selectedFeedId.set(null); // Reset feed selection on source change
    }
</script>

<div class="sidebar">
    <div class="sidebar-header">
        <span class="sidebar-title">FeedVault</span>
        <!-- Theme toggle will go here -->
    </div>

    <nav class="source-list">
        {#if loading}
            <p class="sidebar-status">Loading...</p>
        {:else if error}
            <p class="sidebar-status error">{error}</p>
        {:else if sources.length === 0}
            <p class="sidebar-status">No sources yet.</p>
        {:else}
            {#each sources as source (source.id)}
                <SourceItem
                    {source}
                    active={$selectedSourceId === source.id}
                    on:select={() => selectSource(source.id)}
                />
            {/each}
        {/if}
    </nav>

    <div class="sidebar-footer">
        <button class="add-btn">+ Add source</button>
    </div>
</div>

<style>
    .sidebar {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .sidebar-header {
        padding: 1rem;
        border-bottom: 1px solid var(--border);
        font-weight: 600;
        font-size: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-height: 56px;
    }

    .sidebar-title {
        color: var(--accent);
        letter-spacing: 0.02em;
    }

    .source-list {
        flex: 1;
        overflow-y: auto;
        padding: 0.5rem 0;
    }

    .sidebar-status {
        padding: 1rem;
        color: var(--text-muted);
        font-size: 0.875rem;
    }

    .sidebar-status.error {
        color: var(--danger);
    }

    .sidebar-footer {
        padding: 0.75rem;
        border-top: 1px solid var(--border);
    }

    .add-btn {
        width: 100%;
        padding: 0.5rem;
        border-radius: var(--radius);
        color: var(--text-secondary);
        font-size: 0.875rem;
        text-align: left;
        transition: background var(--transition);
    }

    .add-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
</style>
