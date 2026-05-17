<script>
    export let id;
    export let label;
    export let checked;
    export let hint = null;
</script>

<div class="toggle-wrapper">
    <div class="toggle-row">
        <label for={id} class="form-field-label">{label}</label>
        <label class="switch">
            <input {id} type="checkbox" bind:checked />
            <span class="slider"></span>
        </label>
    </div>
    {#if hint}
        <span class="form-field-hint">{hint}</span>
    {/if}
</div>

<style>
    .toggle-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }

    .toggle-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .switch {
        position: relative;
        display: inline-block;
        width: 32px;
        height: 18px;
        flex-shrink: 0;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
        position: absolute;
    }

    .slider {
        position: absolute;
        inset: 0;
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-radius: 99px;
        transition:
            background var(--transition),
            border-color var(--transition);
        cursor: pointer;
    }

    .slider::before {
        content: '';
        position: absolute;
        width: 12px;
        height: 12px;
        left: 2px;
        top: 50%;
        transform: translateY(-50%);
        background: var(--text-muted);
        border-radius: 50%;
        transition:
            transform var(--transition),
            background var(--transition);
    }

    .switch input:checked + .slider {
        background: var(--accent);
        border-color: var(--accent);
    }

    .switch input:checked + .slider::before {
        transform: translate(14px, -50%);
        background: white;
    }
</style>
