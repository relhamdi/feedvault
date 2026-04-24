<script>
    export let x = 0;
    export let y = 0;
    export let items = []; // { label, action, danger? }
    export let onClose;

    function handleClick(action) {
        action();
        onClose();
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') onClose();
    }

    function handleOutsideClick() {
        onClose();
    }
</script>

<svelte:window on:keydown={handleKeydown} on:click={handleOutsideClick} />

<menu
    class="context-menu"
    style="left: {x}px; top: {y}px"
    on:click|stopPropagation
    on:keydown|stopPropagation
    role="menu"
>
    {#each items as item}
        {#if item.separator}
            <li class="separator" role="separator"></li>
        {:else}
            <li>
                <button
                    class="context-item"
                    class:danger={item.danger}
                    on:click={() => handleClick(item.action)}
                >
                    {#if item.icon}
                        <span class="context-icon">{item.icon}</span>
                    {/if}
                    {item.label}
                </button>
            </li>
        {/if}
    {/each}
</menu>

<style>
    .context-menu {
        position: fixed;
        z-index: 200;
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 0.25rem;
        min-width: 160px;
        list-style: none;
    }

    .context-item {
        width: 100%;
        text-align: left;
        padding: 0.4rem 0.65rem;
        border-radius: calc(var(--radius) - 2px);
        font-size: 0.875rem;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: background var(--transition);
    }

    .context-item:hover {
        background: var(--bg-tertiary);
    }

    .context-item.danger {
        color: var(--danger);
    }

    .context-item.danger:hover {
        background: color-mix(in srgb, var(--danger) 10%, transparent);
    }

    .context-icon {
        font-size: 0.8rem;
        width: 16px;
        text-align: center;
    }

    .separator {
        height: 1px;
        background: var(--border);
        margin: 0.25rem 0;
    }
</style>
