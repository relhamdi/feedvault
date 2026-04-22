<script>
    import { onMount } from 'svelte';

    export let message;
    export let type = 'info'; // info | success | error
    export let duration = 3500;
    export let onDismiss;

    let visible = false;
    let progress = 100;
    let animFrame;
    let startTime;

    onMount(() => {
        requestAnimationFrame(() => (visible = true));

        startTime = Date.now();
        function tick() {
            const elapsed = Date.now() - startTime;
            progress = Math.max(0, 100 - (elapsed / duration) * 100);
            if (elapsed < duration) {
                animFrame = requestAnimationFrame(tick);
            } else {
                dismiss();
            }
        }
        animFrame = requestAnimationFrame(tick);

        return () => cancelAnimationFrame(animFrame);
    });

    function dismiss() {
        visible = false;
        setTimeout(onDismiss, 300);
    }
</script>

<div class="toast" class:visible class:error={type === 'error'} class:success={type === 'success'}>
    <span class="toast-message">{message}</span>
    <button class="toast-close" on:click={dismiss}>✕</button>
    <div class="toast-progress" style="width: {progress}%"></div>
</div>

<style>
    .toast {
        position: relative;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.65rem 0.75rem 0.65rem 1rem;
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        min-width: 260px;
        max-width: 380px;
        overflow: hidden;
        opacity: 0;
        transform: translateX(100%);
        transition:
            opacity 0.25s ease,
            transform 0.25s ease;
    }

    .toast.visible {
        opacity: 1;
        transform: translateX(0);
    }

    .toast.error {
        border-left: 3px solid var(--danger);
    }

    .toast.success {
        border-left: 3px solid var(--success);
    }

    .toast-message {
        flex: 1;
        font-size: 0.875rem;
        color: var(--text-primary);
        line-height: 1.4;
    }

    .toast-close {
        font-size: 0.75rem;
        color: var(--text-muted);
        padding: 0.2rem;
        border-radius: 4px;
        flex-shrink: 0;
        transition: background var(--transition);
    }

    .toast-close:hover {
        background: var(--bg-tertiary);
    }

    .toast-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 2px;
        background: var(--accent);
        transition: width 0.1s linear;
    }

    .toast.error .toast-progress {
        background: var(--danger);
    }
    .toast.success .toast-progress {
        background: var(--success);
    }
</style>
