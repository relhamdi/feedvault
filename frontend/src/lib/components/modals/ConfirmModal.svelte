<script>
    import { createBackdropHandlers } from '../../utils/modal.js';

    export let title = 'Confirm';
    export let message = 'Are you sure?';
    export let confirmLabel = 'Delete';
    export let onConfirm;
    export let onClose;

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
        <h3 class="modal-title">{title}</h3>
        <p class="modal-message">{message}</p>
        <div class="modal-actions">
            <button class="btn-cancel" on:click={onClose}>Cancel</button>
            <button
                class="btn-confirm"
                on:click={() => {
                    onConfirm();
                    onClose();
                }}
            >
                {confirmLabel}
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
        padding: 1.5rem;
        width: 100%;
        max-width: 380px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .modal-title {
        font-size: 1rem;
        font-weight: 600;
    }

    .modal-message {
        font-size: 0.875rem;
        color: var(--text-secondary);
        line-height: 1.5;
    }

    .modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .btn-cancel {
        padding: 0.4rem 0.9rem;
        border-radius: var(--radius);
        font-size: 0.875rem;
        color: var(--text-secondary);
        transition: background var(--transition);
    }

    .btn-cancel:hover {
        background: var(--bg-tertiary);
    }

    .btn-confirm {
        padding: 0.4rem 0.9rem;
        border-radius: var(--radius);
        font-size: 0.875rem;
        background: var(--danger);
        color: white;
        transition: opacity var(--transition);
    }

    .btn-confirm:hover {
        opacity: 0.85;
    }
</style>
