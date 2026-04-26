<script>
    import {
        formatDuration,
        jobStatusClass,
        jobStatusIcon,
        logLevelClass,
    } from '../../utils/format.js';

    export let job;
    export let sources = [];
    export let feeds = [];
    export let open = false;
    export let logs = null; // null = not loaded, [] = loaded empty
    export let loadingLogs = false;

    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    $: sourceName = sources.find((s) => s.id === job.source_id)?.name ?? `Source #${job.source_id}`;
    $: feedName = feeds.find((f) => f.id === job.feed_id)?.name ?? `Feed #${job.feed_id}`;
    $: isActive = job.status === 'running' || job.status === 'pending';
</script>

<div
    class="job-row"
    class:active={isActive}
    class:error={job.status === 'error'}
    on:click={() => dispatch('toggle')}
    on:keydown
    role="button"
    tabindex="0"
>
    <div class="job-main">
        <span class="job-status {jobStatusClass(job.status)}">
            {jobStatusIcon(job.status)}
        </span>

        <div class="job-info">
            <span class="job-name">
                {sourceName}
                <span class="job-separator">›</span>
                {feedName}
            </span>

            <span class="job-meta">
                {job.mode}
                {#if job.target_type}· {job.target_type}{/if}
                · {new Date(job.created_at).toLocaleString()}
                {#if job.items_upserted > 0}· {job.items_upserted} items{/if}
                {#if formatDuration(job)}· {formatDuration(job)}{/if}
            </span>

            {#if job.error_message}
                <span class="job-error">{job.error_message}</span>
            {/if}
        </div>
    </div>
    <span class="job-chevron" class:rotated={open}>▾</span>
</div>

{#if open}
    <div class="job-logs">
        {#if loadingLogs}
            <p class="logs-status">Loading logs...</p>
        {:else if logs === null || logs.length === 0}
            <p class="logs-status">No logs for this job.</p>
        {:else}
            {#each logs as log}
                <div class="log-entry {logLevelClass(log.level)}">
                    <span class="log-time">{new Date(log.created_at).toLocaleTimeString()}</span>
                    <span class="log-level">{log.level}</span>
                    <span class="log-message">{log.message}</span>
                </div>
            {/each}
        {/if}
    </div>
{/if}

<style>
    .job-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0.75rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        background: var(--bg-secondary);
        cursor: pointer;
        transition:
            background var(--transition),
            border-color var(--transition);
        gap: 0.75rem;
    }

    .job-row:hover {
        background: var(--bg-tertiary);
    }
    .job-row.active {
        border-color: var(--accent);
        background: color-mix(in srgb, var(--accent) 5%, var(--bg-secondary));
    }
    .job-row.error {
        border-color: var(--danger);
    }

    .job-main {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        flex: 1;
        min-width: 0;
    }

    .job-status {
        font-size: 0.875rem;
        flex-shrink: 0;
        margin-top: 0.1rem;
    }

    .job-status.success {
        color: var(--success);
    }
    .job-status.danger {
        color: var(--danger);
    }
    .job-status.accent {
        color: var(--accent);
    }
    .job-status.muted {
        color: var(--text-muted);
    }

    .job-info {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
        min-width: 0;
    }

    .job-name {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .job-separator {
        color: var(--text-muted);
        margin: 0 0.25rem;
        font-weight: 300;
    }

    .job-meta {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .job-error {
        font-size: 0.75rem;
        color: var(--danger);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .job-chevron {
        color: var(--text-muted);
        font-size: 0.75rem;
        flex-shrink: 0;
        transition: transform var(--transition);
    }

    .job-chevron.rotated {
        transform: rotate(180deg);
    }

    .job-logs {
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 var(--radius) var(--radius);
        padding: 0.5rem 0.75rem;
        min-height: 85px;
        max-height: 300px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        margin-top: -4px;
    }

    .logs-status {
        font-size: 0.875rem;
        color: var(--text-muted);
        padding: 0.5rem 0;
    }

    .log-entry {
        display: grid;
        grid-template-columns: 80px 60px 1fr;
        gap: 0.5rem;
        font-size: 0.775rem;
        font-family: monospace;
        align-items: baseline;
        padding: 0.15rem 0;
    }

    .log-time {
        color: var(--text-muted);
    }

    .log-level {
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.7rem;
    }

    .log-entry.warning .log-level {
        color: #e8b84b;
    }
    .log-entry.danger .log-level {
        color: var(--danger);
    }
    .log-entry:not(.warning):not(.danger) .log-level {
        color: var(--text-muted);
    }

    .log-message {
        color: var(--text-primary);
        word-break: break-word;
    }
</style>
