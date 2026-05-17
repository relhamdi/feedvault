<script>
    export let poll;

    $: total = poll.num_responses || poll.choices.reduce((sum, c) => sum + c.num_responses, 0);
    $: sorted = [...poll.choices].sort((a, b) => a.position - b.position);

    function pct(count) {
        if (!total) return 0;
        return Math.round((count / total) * 100);
    }

    function formatDate(str) {
        if (!str) return null;
        return new Date(str).toLocaleDateString();
    }
</script>

<div class="poll">
    <div class="poll-header">
        <span class="poll-question">{poll.question}</span>
        <span class="poll-meta">{total} vote{total !== 1 ? 's' : ''}</span>
    </div>

    {#if poll.closes_at}
        <span class="poll-closes">Closes {formatDate(poll.closes_at)}</span>
    {/if}

    <div class="poll-choices">
        {#each sorted as choice}
            {@const p = pct(choice.num_responses)}
            <div class="poll-choice">
                <div class="choice-label">
                    <span class="choice-text">{choice.text_content}</span>
                    <span class="choice-pct">{p}%</span>
                </div>
                <div class="choice-bar-bg">
                    <div class="choice-bar" style="width: {p}%"></div>
                </div>
                <span class="choice-count"
                    >{choice.num_responses} vote{choice.num_responses !== 1 ? 's' : ''}</span
                >
            </div>
        {/each}
    </div>
</div>

<style>
    .poll {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding: 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
    }

    .poll-header {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.5rem;
    }

    .poll-question {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .poll-meta {
        font-size: 0.75rem;
        color: var(--text-muted);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .poll-closes {
        font-size: 0.75rem;
        color: var(--text-muted);
        font-style: italic;
    }

    .poll-choices {
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
    }

    .poll-choice {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }

    .choice-label {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }

    .choice-text {
        font-size: 0.8rem;
        color: var(--text-primary);
    }

    .choice-pct {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--accent);
        flex-shrink: 0;
    }

    .choice-bar-bg {
        height: 6px;
        background: var(--bg-tertiary);
        border-radius: 99px;
        overflow: hidden;
    }

    .choice-bar {
        height: 100%;
        background: var(--accent);
        border-radius: 99px;
        transition: width 0.3s ease;
        min-width: 2px;
    }

    .choice-count {
        font-size: 0.7rem;
        color: var(--text-muted);
    }
</style>
