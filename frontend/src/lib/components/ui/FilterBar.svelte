<script>
    import { itemFilters, resetFilters } from '../../stores/filters.js';
    import { ITEM_SORT_OPTIONS, itemSort } from '../../stores/sorting.js';
    import SortControl from '../ui/SortControl.svelte';
    import TriStateCheckbox from '../ui/TriStateCheckbox.svelte';

    $: hasActiveFilters =
        $itemFilters.search ||
        $itemFilters.tags ||
        $itemFilters.is_read !== null ||
        $itemFilters.is_favorite !== null ||
        $itemFilters.is_nsfw !== null ||
        $itemFilters.is_public !== null;
</script>

<div class="filter-bar">
    <SortControl sort={itemSort} options={ITEM_SORT_OPTIONS} />

    <input
        class="search-input"
        type="search"
        placeholder="Search..."
        bind:value={$itemFilters.search}
    />

    <div class="filter-toggles">
        <TriStateCheckbox bind:value={$itemFilters.is_read} label="Read" id="f-read" />
        <TriStateCheckbox bind:value={$itemFilters.is_favorite} label="Fav" id="f-fav" />
        <TriStateCheckbox bind:value={$itemFilters.is_nsfw} label="NSFW" id="f-nsfw" />
        <TriStateCheckbox bind:value={$itemFilters.is_public} label="Public" id="f-public" />
    </div>

    <input
        class="tags-input"
        type="text"
        placeholder="tag1, tag2..."
        bind:value={$itemFilters.tags}
    />

    {#if hasActiveFilters}
        <button class="clear-btn" on:click={resetFilters} title="Clear filters">✕</button>
    {/if}
</div>

<style>
    .filter-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-bottom: 1px solid var(--border);
        background: var(--bg-secondary);
        flex-wrap: wrap;
    }

    .search-input {
        min-width: 200px;
        padding: 0.3rem 0.6rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--bg-primary);
        color: var(--text-primary);
        font-size: 0.875rem;
    }

    .search-input:focus {
        outline: none;
        border-color: var(--accent);
    }

    .filter-toggles {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-wrap: wrap;
    }

    .tags-input {
        width: 160px;
        padding: 0.3rem 0.6rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--bg-primary);
        color: var(--text-primary);
        font-size: 0.8rem;
    }

    .tags-input:focus {
        outline: none;
        border-color: var(--accent);
    }

    .clear-btn {
        font-size: 0.75rem;
        padding: 0.3rem 0.5rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        color: var(--text-muted);
        transition: all var(--transition);
        flex-shrink: 0;
    }

    .clear-btn:hover {
        border-color: var(--danger);
        color: var(--danger);
    }
</style>
