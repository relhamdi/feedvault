<script>
    import { onDestroy, onMount } from 'svelte';
    import { openMultiSelectId } from '../../stores/ui.js';

    export let options = []; // { value, label }
    export let selected = []; // list of selected values
    export let placeholder = 'All';

    const id = Math.random().toString(36).slice(2);
    let container;

    $: open = $openMultiSelectId === id;
    $: label = selected.length === 0 ? placeholder : `${placeholder} (${selected.length})`;

    function toggle(value) {
        if (selected.includes(value)) {
            selected = selected.filter((v) => v !== value);
        } else {
            selected = [...selected, value];
        }
    }

    function toggleOpen(e) {
        e.stopPropagation();
        openMultiSelectId.set(open ? null : id);
    }

    function handleOutsideClick(e) {
        if (container && !container.contains(e.target)) {
            if (open) openMultiSelectId.set(null);
        }
    }

    onMount(() => document.addEventListener('click', handleOutsideClick));
    onDestroy(() => document.removeEventListener('click', handleOutsideClick));
</script>

<div class="multiselect" bind:this={container}>
    <button class="multiselect-btn" class:active={selected.length > 0} on:click={toggleOpen}>
        {label}
        <span class="chevron" class:rotated={open}>▾</span>
    </button>

    {#if open}
        <div class="multiselect-dropdown">
            {#if options.length === 0}
                <p class="multiselect-empty">No options</p>
            {:else}
                {#each options as option}
                    <label
                        class="multiselect-option"
                        class:checked={selected.includes(option.value)}
                    >
                        <input
                            type="checkbox"
                            checked={selected.includes(option.value)}
                            on:change={() => toggle(option.value)}
                        />
                        {option.label}
                    </label>
                {/each}
            {/if}

            {#if selected.length > 0}
                <button class="multiselect-clear" on:click|stopPropagation={() => (selected = [])}>
                    Clear all
                </button>
            {/if}
        </div>
    {/if}
</div>

<style>
    .multiselect {
        position: relative;
    }

    .multiselect-btn {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.65rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        background: var(--bg-secondary);
        color: var(--text-secondary);
        font-size: 0.8rem;
        transition:
            border-color var(--transition),
            color var(--transition);
        white-space: nowrap;
    }

    .multiselect-btn:hover {
        border-color: var(--accent);
        color: var(--text-primary);
    }

    .multiselect-btn.active {
        border-color: var(--accent);
        color: var(--accent);
    }

    .chevron {
        font-size: 0.7rem;
        transition: transform var(--transition);
    }

    .chevron.rotated {
        transform: rotate(180deg);
    }

    .multiselect-dropdown {
        position: absolute;
        top: calc(100% + 4px);
        left: 0;
        z-index: 50;
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        min-width: 160px;
        max-height: 220px;
        overflow-y: auto;
        padding: 0.25rem;
    }

    .multiselect-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0.5rem;
        border-radius: calc(var(--radius) - 2px);
        font-size: 0.875rem;
        cursor: pointer;
        color: var(--text-primary);
        transition: background var(--transition);
    }

    .multiselect-option:hover {
        background: var(--bg-tertiary);
    }

    .multiselect-option.checked {
        color: var(--accent);
        font-weight: 500;
    }

    .multiselect-option input {
        width: auto;
        accent-color: var(--accent);
    }

    .multiselect-empty {
        padding: 0.5rem;
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .multiselect-clear {
        width: 100%;
        padding: 0.35rem 0.5rem;
        margin-top: 0.25rem;
        border-top: 1px solid var(--border);
        font-size: 0.75rem;
        color: var(--danger);
        text-align: left;
        transition: background var(--transition);
        border-radius: 0;
    }

    .multiselect-clear:hover {
        background: var(--bg-tertiary);
    }
</style>
