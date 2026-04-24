<script>
    export let id;
    export let label;
    export let checked;
</script>

<div class="toggle-row">
    <label for={id} class="toggle-label">{label}</label>
    <input {id} type="checkbox" bind:checked />
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
</style>
