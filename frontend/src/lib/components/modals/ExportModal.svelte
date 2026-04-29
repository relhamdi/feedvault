<script>
    import { onMount } from 'svelte';
    import { dataApi } from '../../api/data.js';
    import { feedsApi } from '../../api/feeds.js';
    import { sourcesApi } from '../../api/sources.js';
    import { toastError, toastSuccess } from '../../stores/toast.js';
    import { createBackdropHandlers } from '../../utils/modal.js';
    import ToggleField from '../ui/ToggleField.svelte';

    export let onClose;

    const { handleMouseDown, handleClick, handleKeydown } = createBackdropHandlers(onClose);

    // Data
    let sources = [];
    let feedsBySource = {}; // { [sourceId]: Feed[] }
    let loading = true;

    // Selection state
    // sourceState: { [sourceId]: 'checked' | 'unchecked' | 'indeterminate' }
    let sourceState = {};
    // feedChecked: { [feedId]: boolean }
    let feedChecked = {};
    // expanded: { [sourceId]: boolean }
    let expanded = {};

    // Export options
    let includeCredentials = false;
    let includeReadStatus = true;
    let includeFavorites = true;
    let includeCollections = true;
    let exporting = false;

    $: selectedFeedIds = Object.entries(feedChecked)
        .filter(([, v]) => v)
        .map(([k]) => parseInt(k));

    $: totalFeeds = Object.keys(feedChecked).length;
    $: selectedCount = selectedFeedIds.length;
    $: isFullExport = selectedCount === Object.keys(feedChecked).length && selectedCount > 0;

    onMount(async () => {
        await loadData();
    });

    async function loadData() {
        loading = true;
        try {
            const [sourcesRes, feedsRes] = await Promise.all([
                sourcesApi.list({ limit: 200 }),
                feedsApi.listAll({ limit: 200 }),
            ]);
            sources = sourcesRes.items;
            // Group feeds by source
            feedsBySource = {};
            for (const feed of feedsRes.items) {
                if (!feedsBySource[feed.source_id]) feedsBySource[feed.source_id] = [];
                feedsBySource[feed.source_id].push(feed);
            }
            // Init all as checked (full export default)
            for (const source of sources) {
                expanded[source.id] = false;
                const feeds = feedsBySource[source.id] ?? [];
                for (const feed of feeds) {
                    feedChecked[feed.id] = true;
                }
            }
            recomputeSourceStates();
        } catch (e) {
            console.error('Failed to load data:', e.message);
            toastError(`Failed to load data: ${e.message}`);
        } finally {
            loading = false;
        }
    }

    // Recompute all source checkbox states from feedChecked
    function recomputeSourceStates() {
        const next = {};
        for (const source of sources) {
            const feeds = feedsBySource[source.id] ?? [];
            if (feeds.length === 0) {
                next[source.id] = 'unchecked';
                continue;
            }
            const checkedCount = feeds.filter((f) => feedChecked[f.id]).length;
            if (checkedCount === 0) next[source.id] = 'unchecked';
            else if (checkedCount === feeds.length) next[source.id] = 'checked';
            else next[source.id] = 'indeterminate';
        }
        sourceState = next;
    }

    // Top-down: clicking a source toggles all its feeds
    function toggleSource(source) {
        const feeds = feedsBySource[source.id] ?? [];
        const current = sourceState[source.id];
        // If checked or indeterminate -> uncheck all; if unchecked -> check all
        const newVal = current === 'unchecked' ? true : false;
        for (const feed of feeds) {
            feedChecked[feed.id] = newVal;
        }
        feedChecked = feedChecked;
        recomputeSourceStates();
    }

    // Bottom-up: toggling a feed recomputes its source state
    function toggleFeed(feed) {
        feedChecked[feed.id] = !feedChecked[feed.id];
        feedChecked = feedChecked;
        recomputeSourceStates();
    }

    function toggleExpanded(sourceId) {
        expanded[sourceId] = !expanded[sourceId];
        expanded = expanded;
    }

    function selectAll() {
        for (const source of sources) {
            for (const feed of feedsBySource[source.id] ?? []) {
                feedChecked[feed.id] = true;
            }
        }
        feedChecked = feedChecked;
        recomputeSourceStates();
    }

    function selectNone() {
        for (const source of sources) {
            for (const feed of feedsBySource[source.id] ?? []) {
                feedChecked[feed.id] = false;
            }
        }
        feedChecked = feedChecked;
        recomputeSourceStates();
    }

    async function handleExport() {
        if (exporting || selectedCount === 0) return;
        exporting = true;
        try {
            const selection = {
                feed_ids: isFullExport ? [] : selectedFeedIds,
                collection_ids: [],
            };

            await dataApi.exportData(selection, {
                includeCredentials,
                includeReadStatus,
                includeFavorites,
                includeCollections,
            });
            toastSuccess('Export downloaded.');
            onClose();
        } catch (e) {
            console.error('Export failed:', e.message);
            toastError(`Export failed: ${e.message}`);
        } finally {
            exporting = false;
        }
    }
</script>

<svelte:window on:keydown={handleKeydown} />

<div
    class="backdrop"
    role="button"
    tabindex="-1"
    aria-label="Close export"
    on:mousedown={handleMouseDown}
    on:click={handleClick}
    on:keydown={handleKeydown}
>
    <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-header">
            <h3 class="modal-title">↓ Export data</h3>
            <button class="close-btn" on:click={onClose}>✕</button>
        </div>

        <div class="modal-body">
            {#if loading}
                <p class="hint">Loading...</p>
            {:else}
                <!-- Selection header -->
                <div class="selection-header">
                    <span class="hint">{selectedCount} / {totalFeeds} feeds selected</span>
                    <div class="selection-actions">
                        <button class="btn-text" on:click={selectAll}>All</button>
                        <span class="sep">·</span>
                        <button class="btn-text" on:click={selectNone}>None</button>
                    </div>
                </div>

                <!-- Tree -->
                <div class="tree">
                    {#each sources as source (source.id)}
                        {@const feeds = feedsBySource[source.id] ?? []}
                        {@const state = sourceState[source.id]}
                        {@const isExpanded = expanded[source.id]}

                        <div class="source-node">
                            <div class="source-row">
                                <button
                                    class="expand-btn"
                                    on:click={() => toggleExpanded(source.id)}
                                    aria-label={isExpanded ? 'Collapse' : 'Expand'}
                                >
                                    {isExpanded ? '▾' : '▸'}
                                </button>
                                <label class="checkbox-label">
                                    <input
                                        type="checkbox"
                                        class="checkbox"
                                        checked={state === 'checked'}
                                        indeterminate={state === 'indeterminate'}
                                        on:change={() => toggleSource(source)}
                                    />
                                    <span
                                        class="source-dot"
                                        style="background:{source.color ?? 'var(--accent)'}"
                                    ></span>
                                    <span class="node-name">{source.name}</span>
                                    <span class="node-count"
                                        >{feeds.length} feed{feeds.length !== 1 ? 's' : ''}</span
                                    >
                                </label>
                            </div>

                            {#if isExpanded && feeds.length > 0}
                                <div class="feed-list">
                                    {#each feeds as feed (feed.id)}
                                        <label class="checkbox-label feed-row">
                                            <input
                                                type="checkbox"
                                                class="checkbox"
                                                checked={feedChecked[feed.id]}
                                                on:change={() => toggleFeed(feed)}
                                            />
                                            <span class="node-name feed-name">{feed.name}</span>
                                            <span class="node-count feed-url">{feed.url}</span>
                                        </label>
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>

                <div class="divider"></div>

                <!-- Options -->
                <div class="options">
                    <ToggleField
                        id="exp-creds"
                        label="Include credentials"
                        bind:checked={includeCredentials}
                    />
                    {#if includeCredentials}
                        <p class="warning-hint">
                            ⚠ Credentials will be in plain text. Keep this file secure.
                        </p>
                    {/if}
                    <ToggleField
                        id="exp-read"
                        label="Include read status"
                        bind:checked={includeReadStatus}
                    />
                    <ToggleField
                        id="exp-fav"
                        label="Include favorites"
                        bind:checked={includeFavorites}
                    />
                    <ToggleField
                        id="exp-col"
                        label="Include collections"
                        bind:checked={includeCollections}
                    />
                </div>
            {/if}
        </div>

        <div class="modal-footer">
            <button class="btn-cancel" on:click={onClose}>Cancel</button>
            <button
                class="btn-export"
                disabled={exporting || selectedCount === 0}
                on:click={handleExport}
            >
                {#if exporting}
                    Exporting...
                {:else if isFullExport}
                    ↓ Export all data
                {:else}
                    ↓ Export {selectedCount} feed{selectedCount !== 1 ? 's' : ''}
                {/if}
            </button>
        </div>
    </div>
</div>

<style>
    .backdrop {
        position: fixed;
        inset: 0;
        background: var(--bg-modal);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 200;
        border: none;
        width: 100%;
        cursor: default;
    }

    .modal {
        background: var(--bg-primary);
        border-radius: var(--radius);
        width: 100%;
        max-width: 480px;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        overflow: hidden;
    }

    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid var(--border);
        flex-shrink: 0;
    }

    .modal-title {
        font-size: 1rem;
        font-weight: 600;
    }

    .close-btn {
        color: var(--text-muted);
        font-size: 0.875rem;
        padding: 0.25rem 0.4rem;
        border-radius: var(--radius);
        transition: background var(--transition);
    }

    .close-btn:hover {
        background: var(--bg-tertiary);
    }

    .modal-body {
        overflow-y: auto;
        padding: 1rem 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        flex: 1;
    }

    .modal-footer {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.75rem;
        padding: 0.875rem 1.25rem;
        border-top: 1px solid var(--border);
        flex-shrink: 0;
    }

    /* Selection header */
    .selection-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .selection-actions {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .btn-text {
        font-size: 0.8rem;
        color: var(--accent);
        padding: 0;
        background: none;
        border: none;
        cursor: pointer;
    }

    .btn-text:hover {
        text-decoration: underline;
    }

    .sep {
        color: var(--text-muted);
        font-size: 0.8rem;
    }

    /* Tree */
    .tree {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
    }

    .source-node {
        border-bottom: 1px solid var(--border);
    }

    .source-node:last-child {
        border-bottom: none;
    }

    .source-row {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.5rem 0.75rem;
        background: var(--bg-secondary);
    }

    .expand-btn {
        font-size: 0.7rem;
        color: var(--text-muted);
        padding: 0.1rem 0.25rem;
        background: none;
        border: none;
        cursor: pointer;
        flex-shrink: 0;
        width: 1.25rem;
    }

    .feed-list {
        display: flex;
        flex-direction: column;
    }

    .feed-row {
        padding: 0.4rem 0.75rem 0.4rem 2.5rem;
        border-top: 1px solid var(--border);
        background: var(--bg-primary);
    }

    .feed-row:hover {
        background: var(--bg-secondary);
    }

    /* Checkbox labels */
    .checkbox-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        flex: 1;
        min-width: 0;
    }

    .checkbox {
        flex-shrink: 0;
        accent-color: var(--accent);
        width: 14px;
        height: 14px;
        cursor: pointer;
    }

    .source-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .node-name {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .feed-name {
        font-weight: 400;
    }

    .node-count {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-left: auto;
        flex-shrink: 0;
    }

    .feed-url {
        max-width: 180px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Options */
    .options {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        padding: 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
    }

    .divider {
        height: 1px;
        background: var(--border);
    }

    .hint {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .warning-hint {
        font-size: 0.775rem;
        color: var(--warning);
        padding: 0.35rem 0.5rem;
        background: rgba(232, 184, 75, 0.08);
        border-radius: var(--radius);
        border: 1px solid rgba(232, 184, 75, 0.25);
    }

    /* Footer buttons */
    .btn-cancel {
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        color: var(--text-secondary);
        transition: background var(--transition);
    }

    .btn-cancel:hover {
        background: var(--bg-tertiary);
    }

    .btn-export {
        font-size: 0.875rem;
        padding: 0.5rem 1.25rem;
        border-radius: var(--radius);
        background: var(--accent);
        color: white;
        transition: opacity var(--transition);
        cursor: pointer;
    }

    .btn-export:hover:not(:disabled) {
        opacity: 0.85;
    }

    .btn-export:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
</style>
