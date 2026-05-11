<!-- UnreadBadge.svelte -->
<script>
    export let count = null; // null = loading
</script>

<span class="unread-badge" class:zero={count === 0}>
    {count ?? '–'}
</span>

<style>
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
