<script>
    import { onMount } from 'svelte';
    import { sourcesApi } from '../../api/sources.js';
    import { selectedFeedId, selectedSourceId } from '../../stores/navigation.js';
    import ConfirmModal from '../ui/ConfirmModal.svelte';
    import ContextMenu from '../ui/ContextMenu.svelte';
    import SourceModal from '../ui/SourceModal.svelte';
    import SourceItem from './SourceItem.svelte';

    let sources = [];
    let loading = true;
    let error = null;

    // Modals
    let showSourceModal = false;
    let editingSource = null;

    // Confirm delete
    let showConfirm = false;
    let deletingSource = null;

    // Context menu
    let contextMenu = null; // { x, y, source }

    onMount(async () => {
        await loadSources();
    });

    async function loadSources() {
        try {
            sources = (await sourcesApi.list()).items;
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    function selectSource(id) {
        selectedSourceId.set(id);
        selectedFeedId.set(null); // Reset feed selection on source change
    }

    function openCreate() {
        editingSource = null;
        showSourceModal = true;
    }

    function openEdit(source) {
        editingSource = source;
        showSourceModal = true;
        contextMenu = null;
    }

    function openDelete(source) {
        deletingSource = source;
        showConfirm = true;
        contextMenu = null;
    }

    async function handleDelete() {
        if (!deletingSource) return;
        const toDelete = deletingSource;
        try {
            await sourcesApi.delete(toDelete.id);
            sources = sources.filter((s) => s.id !== toDelete.id);
            if ($selectedSourceId === toDelete.id) {
                selectedSourceId.set(sources[0]?.id ?? null);
                selectedFeedId.set(null);
            }
        } catch (e) {
            console.error('Delete failed:', e.message);
        }
    }

    function handleSaved(saved) {
        const idx = sources.findIndex((s) => s.id === saved.id);
        if (idx >= 0) {
            sources[idx] = saved;
            sources = sources;
        } else {
            sources = [...sources, saved];
        }
    }

    function handleContextMenu(e, source) {
        e.preventDefault();
        contextMenu = { x: e.clientX, y: e.clientY, source };
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
                    on:contextmenu={(e) => handleContextMenu(e.detail, source)}
                />
            {/each}
        {/if}
    </nav>

    <div class="sidebar-footer">
        <button class="add-btn" on:click={openCreate}>+ Add source</button>
    </div>
</div>

<!-- Context menu -->
{#if contextMenu}
    <ContextMenu
        x={contextMenu.x}
        y={contextMenu.y}
        items={[
            { label: 'Edit', icon: '✎', action: () => openEdit(contextMenu.source) },
            { separator: true },
            {
                label: 'Delete',
                icon: '✕',
                danger: true,
                action: () => openDelete(contextMenu.source),
            },
        ]}
        onClose={() => (contextMenu = null)}
    />
{/if}

<!-- Source modal -->
{#if showSourceModal}
    <SourceModal
        source={editingSource}
        onClose={() => (showSourceModal = false)}
        onSaved={handleSaved}
    />
{/if}

<!-- Confirm delete -->
{#if showConfirm && deletingSource}
    <ConfirmModal
        title="Delete source"
        message="Delete «{deletingSource.name}»? All feeds and items will be permanently deleted."
        onConfirm={handleDelete}
        onClose={() => {
            showConfirm = false;
            deletingSource = null;
        }}
    />
{/if}

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
