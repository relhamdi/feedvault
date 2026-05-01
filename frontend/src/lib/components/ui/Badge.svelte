<script>
    export let type = 'default';
    export let label;
    export let title = '';
</script>

<span class="badge {type}" {title}>{label}</span>

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
        color: var(----warning);
        color: white;
    }
    .badge.inactive {
        background: var(--bg-tertiary);
        color: var(--text-muted);
    }
</style>
