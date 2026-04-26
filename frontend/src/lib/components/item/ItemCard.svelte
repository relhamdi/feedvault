<script>
    import { createEventDispatcher } from 'svelte';
    import { MEDIA_URL } from '../../config.js';
    import { formatDate } from '../../utils/format.js';
    import Badge from '../ui/Badge.svelte';

    export let item;

    const dispatch = createEventDispatcher();

    $: thumbnailSrc = item.thumbnail_path
        ? `${MEDIA_URL}/${item.thumbnail_path}`
        : (item.thumbnail_url ?? null);
</script>

<article
    class="item-card"
    class:unread={!item.is_read}
    class:nsfw={item.is_nsfw}
    on:contextmenu={(e) => {
        e.preventDefault();
        dispatch('contextmenu', e);
    }}
>
    <button class="card-btn" on:click>
        <!-- Thumbnail -->
        <div class="card-thumbnail">
            {#if thumbnailSrc}
                <img src={thumbnailSrc} alt={item.title} />
            {:else}
                <div class="thumbnail-placeholder">
                    <span>{item.title.charAt(0).toUpperCase()}</span>
                </div>
            {/if}

            <!-- Badges overlay -->
            <div class="card-badges">
                {#if item.is_nsfw}
                    <Badge type="nsfw" label="NSFW" />
                {/if}
                {#if !item.is_public}
                    <Badge type="unlisted" label="unlisted" />
                {/if}
                {#if item.is_favorite}
                    <Badge type="favorite" label="♥" />
                {/if}
            </div>
        </div>

        <!-- Content -->
        <div class="card-content">
            <h3 class="card-title">{item.title}</h3>

            {#if item.summary || item.description}
                <p class="card-summary">{item.summary || item.description}</p>
            {/if}

            <div class="card-meta">
                {#if item.author}
                    <span class="card-author">{item.author.name}</span>
                {/if}
                <span class="card-date">{formatDate(item.source_updated_at)}</span>
            </div>

            {#if item.tags?.length > 0}
                <div class="card-tags">
                    {#each item.tags.slice(0, 3) as tag}
                        <span class="tag">{tag}</span>
                    {/each}
                </div>
            {/if}
        </div>
    </button>
</article>

<style>
    .item-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        cursor: pointer;
        transition:
            box-shadow var(--transition),
            transform var(--transition);
        display: flex;
        flex-direction: column;
    }

    .item-card:hover {
        box-shadow: var(--shadow);
        transform: translateY(-2px);
    }

    .item-card.unread {
        border-left: 3px solid var(--accent);
    }

    /* Dim read items slightly */
    .item-card:not(.unread) {
        opacity: 0.7;
    }

    .item-card:not(.unread):hover {
        opacity: 1;
    }

    .card-btn {
        display: flex;
        flex-direction: column;
        width: 100%;
        text-align: left;
    }

    /* Thumbnail */
    .card-thumbnail {
        position: relative;
        width: 100%;
        aspect-ratio: 16 / 9;
        background: var(--bg-tertiary);
        overflow: hidden;
        flex-shrink: 0;
    }

    .card-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .thumbnail-placeholder {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-muted);
    }

    /* Badges */
    .card-badges {
        position: absolute;
        top: 0.4rem;
        left: 0.4rem;
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    /* Content */
    .card-content {
        padding: 0.6rem 0.75rem 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        flex: 1;
    }

    .card-title {
        font-size: 0.875rem;
        font-weight: 600;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        color: var(--text-primary);
    }

    .card-summary {
        font-size: 0.775rem;
        color: var(--text-secondary);
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .card-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        margin-top: auto;
    }

    .card-author {
        font-size: 0.75rem;
        color: var(--text-muted);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100px;
    }

    .card-date {
        font-size: 0.75rem;
        color: var(--text-muted);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .card-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
    }

    .tag {
        font-size: 0.65rem;
        padding: 0.1rem 0.35rem;
        border-radius: 4px;
        background: var(--bg-tertiary);
        color: var(--text-secondary);
        white-space: nowrap;
    }
</style>
