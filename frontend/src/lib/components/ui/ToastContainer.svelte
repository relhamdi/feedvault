<script>
    import { dismissToast, toasts } from '../../stores/toast.js';
    import Toast from './Toast.svelte';
</script>

<div class="toast-container">
    {#each $toasts as t (t.id)}
        <Toast
            message={t.message}
            type={t.type}
            duration={t.duration}
            onDismiss={() => dismissToast(t.id)}
        />
    {/each}
</div>

<style>
    .toast-container {
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 300;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        align-items: flex-end;
    }
</style>
