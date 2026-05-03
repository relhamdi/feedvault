<script>
    import { onMount } from 'svelte';
    import { sourcesApi } from '../../api/sources.js';
    import {
        collectionsMode,
        selectedSourceId,
        selectSource,
        sourceRefreshTrigger,
    } from '../../stores/navigation.js';
    import { SOURCE_SORT_OPTIONS, sourceSort } from '../../stores/sorting.js';
    import { toastError } from '../../stores/toast.js';
    import ConfirmModal from '../modals/ConfirmModal.svelte';
    import LogsModal from '../modals/LogsModal.svelte';
    import SettingsModal from '../modals/SettingsModal.svelte';
    import SourceModal from '../modals/SourceModal.svelte';
    import CollectionItem from '../sidebar/CollectionItem.svelte';
    import SourceItem from '../sidebar/SourceItem.svelte';
    import ContextMenu from '../ui/ContextMenu.svelte';
    import SortControl from '../ui/SortControl.svelte';
    import ThemeToggle from '../ui/ThemeToggle.svelte';

    let sources = [];
    let loading = true;
    let error = null;

    let showLogs = false;
    let showSettings = false;

    // Modals
    let showSourceModal = false;
    let editingSource = null;

    // Confirm delete
    let showConfirm = false;
    let deletingSource = null;

    // Context menu
    let contextMenu = null; // { x, y, source }

    $: if ($sourceRefreshTrigger || $sourceSort) loadSources();

    onMount(async () => {
        await loadSources();
    });

    async function loadSources() {
        try {
            sources = (
                await sourcesApi.list({
                    sort_by: $sourceSort.sort_by,
                    sort_order: $sourceSort.sort_order,
                    limit: 200,
                })
            ).items;
        } catch (e) {
            error = e.message;
            toastError('Failed to load sources');
        } finally {
            loading = false;
        }
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
                selectSource(sources[0]?.id ?? null);
            }
        } catch (e) {
            console.error('Delete failed:', e.message);
            toastError(`Delete failed: ${e.message}`);
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
    <!-- Header -->
    <div class="sidebar-header">
        <span class="sidebar-title">FeedVault</span>
        <ThemeToggle />
    </div>

    <nav class="sidebar-items">
        <!-- Collections entry -->
        <CollectionItem />

        <div class="section-divider"></div>

        <!-- Sorting options -->
        <div class="global-list-controls">
            <span class="list-label">Sources</span>
            <SortControl sort={sourceSort} options={SOURCE_SORT_OPTIONS} />
        </div>

        <!-- Sources entries -->
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
                    active={!$collectionsMode && $selectedSourceId === source.id}
                    on:select={() => selectSource(source.id)}
                    on:contextmenu={(e) => handleContextMenu(e.detail, source)}
                />
            {/each}
        {/if}
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
        <button class="add-btn" on:click={openCreate}>+ Add source</button>
        <div class="footer-actions">
            <button class="icon-btn" on:click={() => (showLogs = true)} title="Logs">📋</button>
            <button class="icon-btn" on:click={() => (showSettings = true)} title="Settings"
                >⚙</button
            >
        </div>
    </div>
</div>

{#if showSettings}
    <SettingsModal onClose={() => (showSettings = false)} />
{/if}

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

{#if showLogs}
    <LogsModal onClose={() => (showLogs = false)} />
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

    .list-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
    }

    .sidebar-items {
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
        display: flex;
        align-items: center;
        gap: 0.5rem;
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

    .footer-actions {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-shrink: 0;
    }

    .icon-btn {
        padding: 0.4rem;
        border-radius: var(--radius);
        color: var(--text-muted);
        font-size: 1rem;
        transition:
            background var(--transition),
            color var(--transition);
    }

    .icon-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .section-divider {
        height: 1px;
        background: var(--border);
    }
</style>
