<script>
    // value: null = no filter, true = filter true, false = filter false
    export let value = null;
    export let label = '';
    export let id = '';

    function cycle() {
        if (value === null) value = true;
        else if (value === true) value = false;
        else value = null;
    }
</script>

<button class="tri-state" class:active={value !== null} on:click={cycle} {id} type="button">
    <span class="tri-icon">
        {#if value === null}☐
        {:else if value === true}☑
        {:else}☒
        {/if}
    </span>
    <span class="tri-label">{label}</span>
</button>

<style>
    .tri-state {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
        color: var(--text-muted);
        padding: 0.2rem 0.4rem;
        border-radius: var(--radius);
        border: 1px solid transparent;
        transition: all var(--transition);
        white-space: nowrap;
    }

    .tri-state:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .tri-state.active {
        border-color: var(--accent);
        color: var(--accent);
        background: color-mix(in srgb, var(--accent) 8%, transparent);
    }

    .tri-icon {
        font-size: 0.9rem;
        line-height: 1;
    }
</style>
