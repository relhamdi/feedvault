<script>
    import { onMount } from 'svelte';
    import { collectionsApi } from '../../api/collections.js';
    import {
        collectionRefreshTrigger,
        selectCollection,
        selectedCollectionId,
        triggerCollectionRefresh,
    } from '../../stores/navigation.js';
    import { refreshCollectionStats } from '../../stores/stats.js';
    import { toastError } from '../../stores/toast.js';
    import CollectionTab from '../collection/CollectionTab.svelte';
    import CollectionModal from '../modals/CollectionModal.svelte';
    import ConfirmModal from '../modals/ConfirmModal.svelte';
    import ContextMenu from '../ui/ContextMenu.svelte';

    let collections = [];
    let loading = true;
    let error = null;

    let showCollectionModal = false;
    let editingCollection = null;

    let showConfirm = false;
    let deletingCollection = null;

    let contextMenu = null;

    let initialized = false;

    $: if (initialized && $collectionRefreshTrigger) loadCollections();

    onMount(async () => {
        await loadCollections();
        initialized = true;
    });

    async function loadCollections() {
        loading = true;
        error = null;
        try {
            collections = (await collectionsApi.list()).items;
            // Auto-select first if none selected or current no longer exists
            if (collections.length > 0) {
                const stillExists = collections.find((c) => c.id === $selectedCollectionId);
                if (!stillExists) selectCollection(collections[0].id);
            }
        } catch (e) {
            error = e.message;
            toastError('Failed to load collections');
        } finally {
            loading = false;
        }
    }

    function openCreate() {
        editingCollection = null;
        showCollectionModal = true;
        contextMenu = null;
    }

    function openEdit(collection) {
        editingCollection = collection;
        showCollectionModal = true;
        contextMenu = null;
    }

    function openDelete(collection) {
        deletingCollection = collection;
        showConfirm = true;
        contextMenu = null;
    }

    async function handleDelete() {
        if (!deletingCollection) return;
        const toDelete = deletingCollection;
        try {
            await collectionsApi.delete(toDelete.id);
            collections = collections.filter((c) => c.id !== toDelete.id);
            if ($selectedCollectionId === toDelete.id) {
                selectCollection(collections[0]?.id ?? null);
            }
        } catch (e) {
            console.error('Delete failed:', e.message);
            toastError(`Delete failed: ${e.message}`);
        }
    }

    function handleSaved(saved) {
        const idx = collections.findIndex((c) => c.id === saved.id);
        if (idx >= 0) {
            collections[idx] = saved;
            collections = collections;
        } else {
            collections = [...collections, saved];
            selectCollection(saved.id);
        }
        refreshCollectionStats(saved.id);
        triggerCollectionRefresh();
    }

    function handleContextMenu(e, collection) {
        contextMenu = { x: e.detail.clientX, y: e.detail.clientY, collection };
    }

    function handleWheel(e) {
        if (e.deltaY === 0) return;
        e.preventDefault();
        e.currentTarget.scrollLeft += e.deltaY;
    }
</script>

<div class="collection-tabs-wrapper">
    <button class="add-tab-btn" title="New collection" on:click={openCreate}>+</button>

    <div class="collection-tabs" on:wheel={handleWheel}>
        {#if loading}
            <span class="tabs-status">Loading...</span>
        {:else if error}
            <span class="tabs-status error">{error}</span>
        {:else if collections.length === 0}
            <span class="tabs-status">No collections yet.</span>
        {:else}
            {#each collections as collection (collection.id)}
                <CollectionTab
                    {collection}
                    active={$selectedCollectionId === collection.id}
                    on:select={() => selectCollection(collection.id)}
                    on:contextmenu={(e) => handleContextMenu(e, collection)}
                />
            {/each}
        {/if}
    </div>
</div>

{#if contextMenu}
    <ContextMenu
        x={contextMenu.x}
        y={contextMenu.y}
        items={[
            { label: 'Edit', icon: '✎', action: () => openEdit(contextMenu.collection) },
            { separator: true },
            {
                label: 'Delete',
                icon: '✕',
                danger: true,
                action: () => openDelete(contextMenu.collection),
            },
        ]}
        onClose={() => (contextMenu = null)}
    />
{/if}

{#if showCollectionModal}
    <CollectionModal
        collection={editingCollection}
        onClose={() => (showCollectionModal = false)}
        onSaved={handleSaved}
    />
{/if}

{#if showConfirm && deletingCollection}
    <ConfirmModal
        title="Delete collection"
        message="Delete «{deletingCollection.name}»? Items are not affected."
        onConfirm={handleDelete}
        onClose={() => {
            showConfirm = false;
            deletingCollection = null;
        }}
    />
{/if}

<style>
    .collection-tabs-wrapper {
        display: flex;
        align-items: center;
        border-bottom: 1px solid var(--border);
        background: var(--bg-secondary);
        min-height: 48px;
    }

    .collection-tabs {
        display: flex;
        align-items: center;
        overflow-x: auto;
        flex: 1;
        gap: 0.25rem;
        padding: 0.375rem 0.5rem;
        scrollbar-width: none;
    }

    .collection-tabs::-webkit-scrollbar {
        display: none;
    }

    .tabs-status {
        padding: 0 0.5rem;
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .tabs-status.error {
        color: var(--danger);
    }

    .add-tab-btn {
        flex-shrink: 0;
        width: 48px;
        height: 48px;
        border-radius: 0;
        border-right: 1px solid var(--border);
        padding-bottom: 5px;
        color: var(--text-muted);
        font-size: 1.25rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition:
            background var(--transition),
            color var(--transition);
    }

    .add-tab-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
</style>
