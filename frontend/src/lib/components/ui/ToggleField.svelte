<script>
    export let id;
    export let label;
    export let checked;
    export let hint = null;
</script>

<div class="toggle-row">
    <label for={id} class="toggle-label">{label}</label>
    <input {id} type="checkbox" bind:checked />
    {#if hint}
        <span class="toggle-hint">{hint}</span>
    {/if}
</div>

<style>
    .toggle-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .toggle-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-secondary);
    }

    .toggle-hint {
        font-size: 0.75rem;
        color: var(--text-muted);
    }
</style>
