<script>
    export let sort; // writable store { sort_by, sort_order }
    export let options; // [{ value, label }]

    function toggleOrder() {
        sort.update((s) => ({ ...s, sort_order: s.sort_order === 'asc' ? 'desc' : 'asc' }));
    }

    function setField(value) {
        sort.update((s) => ({ ...s, sort_by: value }));
    }
</script>

<div class="sort-control">
    <select value={$sort.sort_by} on:change={(e) => setField(e.target.value)}>
        {#each options as opt}
            <option value={opt.value}>{opt.label}</option>
        {/each}
    </select>
    <button
        class="order-btn"
        on:click={toggleOrder}
        title={$sort.sort_order === 'asc' ? 'Ascending' : 'Descending'}
    >
        {$sort.sort_order === 'asc' ? '↑' : '↓'}
    </button>
</div>

<style>
    .sort-control {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    select {
        font-size: 0.75rem;
        padding: 0.2rem 0.4rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--bg-secondary);
        color: var(--text-secondary);
        cursor: pointer;
    }

    .order-btn {
        font-size: 0.875rem;
        padding: 0.2rem 0.35rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        color: var(--text-muted);
        transition:
            background var(--transition),
            color var(--transition);
    }

    .order-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
</style>
