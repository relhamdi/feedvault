<script>
    import { theme } from '../../stores/theme.js';

    function toggle() {
        theme.update((t) => (t === 'light' ? 'dark' : 'light'));
    }
</script>

<button
    class="theme-toggle"
    on:click={toggle}
    title={$theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
    aria-label="Toggle theme"
>
    <span class="track">
        <span class="thumb">
            {$theme === 'light' ? '☀' : '🌙'}
        </span>
    </span>
    <span class="label">{$theme === 'light' ? 'Light' : 'Dark'}</span>
</button>

<style>
    .theme-toggle {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: none;
        border: none;
        cursor: pointer;
        padding: 0.25rem;
        border-radius: var(--radius);
        transition: background var(--transition);
    }

    .theme-toggle:hover {
        background: var(--bg-tertiary);
    }

    .track {
        width: 36px;
        height: 20px;
        background: var(--bg-tertiary);
        border-radius: 99px;
        border: 1px solid var(--border);
        display: flex;
        align-items: center;
        padding: 2px;
        transition: background var(--transition);
    }

    :global([data-theme='dark']) .track {
        background: var(--accent);
        border-color: var(--accent);
    }

    .thumb {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background: var(--bg-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        transition: transform var(--transition);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    :global([data-theme='dark']) .thumb {
        transform: translateX(16px);
    }

    .label {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }
</style>
