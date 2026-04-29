<script>
    import { onDestroy, onMount } from 'svelte';
    import { feedsApi } from '../../api/feeds.js';
    import { scrapeApi } from '../../api/scrape.js';
    import { sourcesApi } from '../../api/sources.js';
    import { getPollInterval } from '../../stores/scraping.js';
    import { createBackdropHandlers } from '../../utils/modal.js';
    import JobRow from '../log/JobRow.svelte';
    import MultiSelect from '../ui/MultiSelect.svelte';

    export let onClose;

    const { handleMouseDown, handleClick, handleKeydown } = createBackdropHandlers(onClose);

    // --- Data ---
    let activeJobs = [];
    let historyJobs = [];
    let sources = [];
    let feeds = [];
    let loading = true;

    let historyOffset = 0;
    const JOBS_LIMIT = 10;
    let totalJobs = 0;
    let loadingMore = false;

    // --- Filters ---
    let selectedStatuses = [];
    let selectedSourceIds = [];
    let selectedFeedIds = [];

    const STATUS_OPTIONS = [
        { value: 'done', label: 'Done' },
        { value: 'error', label: 'Error' },
        { value: 'pending', label: 'Pending' },
    ];

    // --- Accordion ---
    let openJobId = null;
    let jobLogs = {}; // { [jobId]: ScrapeLog[] }
    let loadingLogs = new Set();

    // --- Poll active jobs ---
    let cleanups = [];
    let refreshInterval = null;

    $: sourceOptions = sources.map((s) => ({ value: String(s.id), label: s.name }));
    $: feedOptions = feeds.map((f) => ({ value: String(f.id), label: f.name }));

    $: filteredHistory = historyJobs.filter((job) => {
        if (selectedStatuses.length > 0 && !selectedStatuses.includes(job.status)) return false;
        if (selectedSourceIds.length > 0 && !selectedSourceIds.includes(String(job.source_id)))
            return false;
        if (selectedFeedIds.length > 0 && !selectedFeedIds.includes(String(job.feed_id)))
            return false;
        return true;
    });

    async function toggleJob(jobId) {
        if (openJobId === jobId) {
            openJobId = null;
            return;
        }
        openJobId = jobId;
        if (!jobLogs[jobId]) {
            await loadJobLogs(jobId);
        }
    }

    async function loadJobLogs(jobId) {
        loadingLogs.add(jobId);
        loadingLogs = loadingLogs;
        try {
            jobLogs[jobId] = await scrapeApi.getLogs(jobId);
            jobLogs = jobLogs;
        } catch (e) {
            jobLogs[jobId] = [];
            console.error('Failed to load job logs:', e.message);
            toastError(`Failed to load job logs: ${e.message}`);
        } finally {
            loadingLogs.delete(jobId);
            loadingLogs = loadingLogs;
        }
    }

    // Load data
    async function loadAll() {
        historyOffset = 0;
        try {
            const [jobsRes, sourcesRes, feedsRes] = await Promise.all([
                scrapeApi.listJobs({ limit: JOBS_LIMIT, offset: 0 }),
                sourcesApi.list({ limit: 200 }),
                feedsApi.listAll({ limit: 200 }),
            ]);
            const jobs = jobsRes.items ?? jobsRes;
            totalJobs = jobsRes.total ?? jobs.length;
            activeJobs = jobs.filter((j) => j.status === 'running' || j.status === 'pending');
            historyJobs = jobs.filter((j) => j.status !== 'running' && j.status !== 'pending');
            historyOffset = historyJobs.length;
            sources = sourcesRes.items;
            feeds = feedsRes.items;
        } catch (e) {
            console.error('Failed to load resources:', e.message);
            toastError(`Failed to load resources: ${e.message}`);
        } finally {
            loading = false;
        }
    }

    async function loadMoreJobs() {
        if (loadingMore || historyOffset >= totalJobs) return;
        loadingMore = true;
        try {
            const res = await scrapeApi.listJobs({ limit: JOBS_LIMIT, offset: historyOffset });
            const jobs = (res.items ?? res).filter(
                (j) => j.status !== 'running' && j.status !== 'pending'
            );
            historyJobs = [...historyJobs, ...jobs];
            historyOffset += jobs.length;
        } catch (e) {
            console.error('Failed to load more jobs:', e.message);
            toastError(`Failed to load more jobs: ${e.message}`);
        } finally {
            loadingMore = false;
        }
    }

    function handleHistoryScroll(e) {
        const el = e.target;
        const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
        if (nearBottom && historyOffset < totalJobs && !loadingMore) {
            loadMoreJobs();
        }
    }

    function startPolling() {
        refreshInterval = setInterval(async () => {
            if (activeJobs.length === 0) return;
            await loadAll();
        }, getPollInterval());
    }

    onMount(async () => {
        await loadAll();
        startPolling();
    });

    onDestroy(() => {
        if (refreshInterval) clearInterval(refreshInterval);
        cleanups.forEach((fn) => fn());
    });
</script>

<svelte:window on:keydown={handleKeydown} />

<div
    class="backdrop"
    role="button"
    tabindex="-1"
    aria-label="Close logs"
    on:mousedown={handleMouseDown}
    on:click={handleClick}
    on:keydown={handleKeydown}
>
    <div class="modal" role="dialog" aria-modal="true">
        <!-- Header -->
        <div class="modal-header">
            <h3 class="modal-title">📋 Scrape Logs</h3>
            <button class="close-btn" on:click={onClose}>✕</button>
        </div>

        <!-- Filters -->
        <div class="filters-bar">
            <MultiSelect
                options={STATUS_OPTIONS}
                bind:selected={selectedStatuses}
                placeholder="Status"
            />
            <MultiSelect
                options={sourceOptions}
                bind:selected={selectedSourceIds}
                placeholder="Source"
            />
            <MultiSelect options={feedOptions} bind:selected={selectedFeedIds} placeholder="Feed" />
            <button class="btn-refresh" on:click={loadAll} title="Refresh">↻</button>
        </div>

        <!-- Body -->
        <div class="modal-body" on:scroll={handleHistoryScroll}>
            {#if loading}
                <p class="logs-status">Loading...</p>
            {:else}
                <!-- Active jobs -->
                <div class="section-label">
                    Active
                    {#if activeJobs.length > 0}
                        <span class="filter-count">({activeJobs.length})</span>
                    {/if}
                </div>
                {#if activeJobs.length === 0}
                    <p class="logs-status">No active jobs.</p>
                {:else}
                    {#each activeJobs as job (job.id)}
                        <JobRow
                            {job}
                            {sources}
                            {feeds}
                            open={openJobId === job.id}
                            logs={jobLogs[job.id] ?? null}
                            loadingLogs={loadingLogs.has(job.id)}
                            on:toggle={() => toggleJob(job.id)}
                        />
                    {/each}
                {/if}

                <!-- History -->
                <div class="section-label">
                    History
                    <span class="filter-count">
                        ({filteredHistory.length}{filteredHistory.length !== historyJobs.length
                            ? `/${historyJobs.length}`
                            : ''})
                    </span>
                </div>

                {#if filteredHistory.length === 0}
                    <p class="logs-status">No jobs match the current filters.</p>
                {:else}
                    {#each filteredHistory as job (job.id)}
                        <JobRow
                            {job}
                            {sources}
                            {feeds}
                            open={openJobId === job.id}
                            logs={jobLogs[job.id] ?? null}
                            loadingLogs={loadingLogs.has(job.id)}
                            on:toggle={() => toggleJob(job.id)}
                        />
                    {/each}
                {/if}
            {/if}
            {#if loadingMore}
                <p class="logs-status">Loading more...</p>
            {/if}
        </div>
    </div>
</div>

<style>
    .backdrop {
        position: fixed;
        inset: 0;
        background: var(--bg-modal);
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
        max-width: 900px;
        height: 80vh;
        min-height: 500px;
        display: flex;
        flex-direction: column;
        box-shadow: var(--big-shadow);
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

    /* Filters */
    .filters-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem 1.25rem;
        border-bottom: 1px solid var(--border);
        flex-shrink: 0;
        flex-wrap: wrap;
    }

    .btn-refresh {
        margin-left: auto;
        padding: 0.35rem 0.65rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        color: var(--text-muted);
        font-size: 0.875rem;
        transition:
            background var(--transition),
            color var(--transition);
    }

    .btn-refresh:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    /* Body */
    .modal-body {
        overflow-y: auto;
        padding: 1rem 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        flex: 1;
    }

    .logs-status {
        text-align: center;
        font-size: 0.875rem;
        color: var(--text-muted);
        padding: 0.5rem 0;
    }

    /* Section label */
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        padding: 0.75rem 0 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .filter-count {
        font-weight: 400;
        text-transform: none;
        letter-spacing: 0;
    }
</style>
