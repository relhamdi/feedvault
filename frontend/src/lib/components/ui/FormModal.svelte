<script>
    import { createBackdropHandlers } from '../../utils/modal.js';

    export let title;
    export let onClose;
    export let onSubmit;
    export let submitLabel = 'Save';
    export let loading = false;

    let mouseDownOnBackdrop = false;

    const { handleMouseDown, handleClick, handleKeydown } = createBackdropHandlers(onClose);
</script>

<svelte:window on:keydown={handleKeydown} />

<div
    class="backdrop"
    on:mousedown={handleMouseDown}
    on:click={handleClick}
    on:keydown={handleKeydown}
    role="button"
    tabindex="-1"
    aria-label="Close"
>
    <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-header">
            <h3 class="modal-title">{title}</h3>
            <button class="close-btn" on:click={onClose}>✕</button>
        </div>

        <div class="modal-body">
            <slot />
        </div>

        <div class="modal-footer">
            <button class="btn-cancel" on:click={onClose} disabled={loading}> Cancel </button>
            <button class="btn-submit" on:click={onSubmit} disabled={loading}>
                {#if loading}Saving...{:else}{submitLabel}{/if}
            </button>
        </div>
    </div>
</div>

<style>
    .backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 150;
        border: none;
        width: 100%;
        cursor: default;
    }

    .modal {
        background: var(--bg-primary);
        border-radius: var(--radius);
        width: 100%;
        max-width: 480px;
        max-height: 90vh;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
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
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        flex: 1;
    }

    .modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
        border-top: 1px solid var(--border);
        flex-shrink: 0;
    }

    .btn-cancel {
        padding: 0.4rem 0.9rem;
        border-radius: var(--radius);
        font-size: 0.875rem;
        color: var(--text-secondary);
        transition: background var(--transition);
    }

    .btn-cancel:hover:not(:disabled) {
        background: var(--bg-tertiary);
    }

    .btn-submit {
        padding: 0.4rem 0.9rem;
        border-radius: var(--radius);
        font-size: 0.875rem;
        background: var(--accent);
        color: white;
        transition: opacity var(--transition);
    }

    .btn-submit:hover:not(:disabled) {
        opacity: 0.85;
    }

    .btn-submit:disabled,
    .btn-cancel:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>
