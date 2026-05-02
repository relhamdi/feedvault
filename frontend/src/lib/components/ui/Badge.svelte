<script>
    export let type = 'default';
    export let label;
    export let bgColor;
    export let title = '';
</script>

<span class="badge {type}" {title} style="--bgColor: {bgColor}">{label}</span>

<style>
    .badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 0.15rem 0.35rem;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        text-align: center;
        display: inline-block;
    }

    .badge.nsfw {
        background: var(--danger);
        color: white;
    }
    .badge.unlisted {
        background: var(--text-muted);
        color: white;
    }
    .badge.favorite {
        background: var(--warning);
        color: white;
    }
    .badge.inactive {
        background: var(--bg-tertiary);
        color: var(--text-muted);
    }

    .badge.source {
        background: var(--bgColor, var(--accent));
        color: white;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.4rem;
        text-transform: none;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
</style>
