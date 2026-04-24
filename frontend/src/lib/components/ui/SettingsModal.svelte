<script>
    import { onMount } from 'svelte';
    import { rootApi } from '../../api/client.js';
    import { sourcesApi } from '../../api/sources.js';
    import { triggerSourceRefresh } from '../../stores/navigation.js';
    import { getPollInterval, setPollInterval } from '../../stores/scraping.js';
    import { toastError, toastSuccess } from '../../stores/toast.js';
    import { createBackdropHandlers } from '../../utils/modal.js';
    import ThemeToggle from './ThemeToggle.svelte';

    export let onClose;

    const { handleMouseDown, handleClick, handleKeydown } = createBackdropHandlers(onClose);

    // --- Sources bootstrap ---
    let registeredSlugs = []; // Slugs in registry (from bootstrap endpoint)
    let existingSources = []; // Sources already in DB
    let bootstrapping = new Set(); // Slugs currently bootstrapping
    let loadingSources = true;

    let healthStatus = null; // null | 'ok' | 'error'
    let healthCheckedAt = null;
    let checkingHealth = false;

    // Stats for health display
    let dbStats = null;

    // Persisted in localStorage
    let pollInterval = getPollInterval();

    $: existingSlugs = new Set(existingSources.map((s) => s.slug));
    $: availableSlugs = registeredSlugs.filter((slug) => !existingSlugs.has(slug));
    $: allBootstrapped = availableSlugs.length === 0;

    onMount(async () => {
        await Promise.all([loadSourcesData(), checkHealth()]);
    });

    async function checkHealth() {
        checkingHealth = true;
        try {
            const [health, stats] = await Promise.all([rootApi.health(), rootApi.stats()]);

            healthStatus = 'ok';
            dbStats = stats;
        } catch (e) {
            healthStatus = 'error';
            dbStats = null;
            console.error('Health check failed:', e.message);
            toastError(`Health check failed: ${e.message}`);
        } finally {
            healthCheckedAt = new Date();
            checkingHealth = false;
        }
    }

    async function loadSourcesData() {
        loadingSources = true;
        try {
            const [registryRes, sourcesRes] = await Promise.all([
                sourcesApi.registeredSlugs(),
                sourcesApi.list({ limit: 200 }),
            ]);
            registeredSlugs = registryRes;
            existingSources = sourcesRes.items;
        } catch (e) {
            console.error('Failed to load sources:', e.message);
            toastError(`Failed to load sources: ${e.message}`);
        } finally {
            loadingSources = false;
        }
    }

    async function bootstrapSource(slug) {
        if (bootstrapping.has(slug)) return;
        bootstrapping.add(slug);
        bootstrapping = bootstrapping;
        try {
            await sourcesApi.bootstrap(slug);
            toastSuccess(`Source '${slug}' bootstrapped successfully.`);
            await loadSourcesData();
            triggerSourceRefresh();
        } catch (e) {
            console.error(`Bootstrap failed for '${slug}'`, e.message);
            toastError(`Bootstrap failed for '${slug}': ${e.message}`);
        } finally {
            bootstrapping.delete(slug);
            bootstrapping = bootstrapping;
        }
    }

    async function bootstrapAll() {
        await Promise.all(availableSlugs.map((slug) => bootstrapSource(slug)));
    }

    function savePollInterval() {
        const val = Math.max(500, Math.min(10000, pollInterval));
        pollInterval = val;
        setPollInterval(val);
        toastSuccess('Polling interval saved.');
    }
</script>

<svelte:window on:keydown={handleKeydown} />

<div
    class="backdrop"
    role="button"
    tabindex="-1"
    aria-label="Close settings"
    on:mousedown={handleMouseDown}
    on:click={handleClick}
    on:keydown={handleKeydown}
>
    <div class="modal" role="dialog" aria-modal="true">
        <!-- Header -->
        <div class="modal-header">
            <h3 class="modal-title">⚙ Settings</h3>
            <button class="close-btn" on:click={onClose}>✕</button>
        </div>

        <!-- Body -->
        <div class="modal-body">
            <!-- General -->
            <section class="settings-section">
                <h4 class="settings-section-title">General</h4>
                <div class="settings-row">
                    <span class="settings-label">Theme</span>
                    <ThemeToggle />
                </div>
            </section>

            <div class="settings-divider"></div>

            <!-- Health -->
            <section class="settings-section">
                <div class="settings-section-header">
                    <h4 class="settings-section-title">API</h4>
                    <button class="btn-check" on:click={checkHealth} disabled={checkingHealth}>
                        {checkingHealth ? 'Checking...' : 'Check now'}
                    </button>
                </div>

                <div class="health-row">
                    <span
                        class="health-indicator"
                        class:ok={healthStatus === 'ok'}
                        class:error={healthStatus === 'error'}
                    >
                        {#if healthStatus === null}
                            ○ Checking...
                        {:else if healthStatus === 'ok'}
                            ● Online
                        {:else}
                            ● Offline
                        {/if}
                    </span>
                    {#if healthCheckedAt}
                        <span class="settings-hint">
                            Last checked: {healthCheckedAt.toLocaleTimeString()}
                        </span>
                    {/if}
                </div>

                {#if dbStats}
                    <div class="db-stats">
                        <div class="db-stat">
                            <span class="db-stat-value">{dbStats.sources}</span>
                            <span class="db-stat-label">sources</span>
                        </div>
                        <div class="db-stat">
                            <span class="db-stat-value">{dbStats.feeds}</span>
                            <span class="db-stat-label">feeds</span>
                        </div>
                        <div class="db-stat">
                            <span class="db-stat-value">{dbStats.items}</span>
                            <span class="db-stat-label">items</span>
                        </div>
                        <div class="db-stat">
                            <span class="db-stat-value">{dbStats.unread}</span>
                            <span class="db-stat-label">unread</span>
                        </div>
                        <div class="db-stat">
                            <span class="db-stat-value">{dbStats.favorite}</span>
                            <span class="db-stat-label">favorites</span>
                        </div>
                    </div>
                {/if}
            </section>

            <!-- Sources -->
            <section class="settings-section">
                <div class="settings-section-header">
                    <h4 class="settings-section-title">Sources</h4>
                    <button
                        class="btn-bootstrap-all"
                        disabled={allBootstrapped || bootstrapping.size > 0}
                        on:click={bootstrapAll}
                    >
                        {bootstrapping.size > 0 ? 'Bootstrapping...' : 'Bootstrap all'}
                    </button>
                </div>

                {#if loadingSources}
                    <p class="settings-hint">Loading...</p>
                {:else if allBootstrapped}
                    <p class="settings-hint success">✓ All sources are configured.</p>
                {:else}
                    <div class="source-list">
                        {#each availableSlugs as slug}
                            <div class="source-row">
                                <div class="source-info">
                                    <span class="source-name">{slug}</span>
                                </div>
                                <button
                                    class="btn-bootstrap"
                                    disabled={bootstrapping.has(slug)}
                                    on:click={() => bootstrapSource(slug)}
                                >
                                    {bootstrapping.has(slug) ? '...' : 'Bootstrap'}
                                </button>
                            </div>
                        {/each}
                    </div>
                {/if}
            </section>

            <div class="settings-divider"></div>

            <!-- Scraping -->
            <section class="settings-section">
                <h4 class="settings-section-title">Scraping</h4>

                <div class="settings-row">
                    <div class="settings-label-group">
                        <span class="settings-label">Polling interval</span>
                        <span class="settings-hint">How often to check scrape job status (ms)</span>
                    </div>
                    <div class="poll-input-row">
                        <input
                            type="number"
                            bind:value={pollInterval}
                            min="500"
                            max="10000"
                            step="500"
                            class="poll-input"
                        />
                        <button class="btn-save" on:click={savePollInterval}>Save</button>
                    </div>
                </div>
            </section>
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
        max-width: 520px;
        max-height: 85vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
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
        gap: 1.25rem;
    }

    /* Sections */
    .settings-section {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .settings-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .settings-section-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
    }

    .settings-divider {
        height: 1px;
        background: var(--border);
    }

    .settings-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0;
    }

    .settings-label {
        font-size: 0.875rem;
        color: var(--text-primary);
    }

    .settings-hint {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .settings-hint.success {
        color: var(--success);
    }

    /* Bootstrap */
    .btn-bootstrap-all {
        font-size: 0.8rem;
        padding: 0.35rem 0.75rem;
        border-radius: var(--radius);
        background: var(--accent);
        color: white;
        transition: opacity var(--transition);
    }

    .btn-bootstrap-all:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .btn-bootstrap-all:hover:not(:disabled) {
        opacity: 0.85;
    }

    .source-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .source-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.75rem;
        border-radius: var(--radius);
        background: var(--bg-secondary);
        border: 1px solid var(--border);
    }

    .source-info {
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }

    .source-name {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
    }

    .btn-bootstrap {
        font-size: 0.8rem;
        padding: 0.3rem 0.65rem;
        border-radius: var(--radius);
        border: 1px solid var(--accent);
        color: var(--accent);
        transition:
            background var(--transition),
            color var(--transition);
    }

    .btn-bootstrap:hover:not(:disabled) {
        background: var(--accent);
        color: white;
    }

    .btn-bootstrap:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    /* Health */
    .health-row {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .health-indicator {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .health-indicator.ok {
        color: var(--success);
    }
    .health-indicator.error {
        color: var(--danger);
    }

    .db-stats {
        display: flex;
        justify-content: space-evenly;
        gap: 1.25rem;
        flex-wrap: wrap;
        padding: 0.75rem;
        background: var(--bg-secondary);
        border-radius: var(--radius);
        border: 1px solid var(--border);
    }

    .db-stat {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.1rem;
    }

    .db-stat-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .db-stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: capitalize;
    }

    /* Buttons */
    .btn-check {
        font-size: 0.8rem;
        padding: 0.35rem 0.75rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        color: var(--text-secondary);
        transition:
            background var(--transition),
            color var(--transition);
    }

    .btn-check:hover:not(:disabled) {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .btn-check:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    /* Scraping */
    .settings-label-group {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
    }

    .poll-input-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .poll-input {
        width: 80px;
        padding: 0.35rem 0.5rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--bg-secondary);
        color: var(--text-primary);
        font-size: 0.875rem;
        text-align: center;
    }

    .btn-save {
        font-size: 0.8rem;
        padding: 0.35rem 0.65rem;
        border-radius: var(--radius);
        background: var(--accent);
        color: white;
        transition: opacity var(--transition);
    }

    .btn-save:hover {
        opacity: 0.85;
    }
</style>
