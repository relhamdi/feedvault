<script>
    import { onMount } from 'svelte';
    import { itemsApi } from '../../api/items.js';
    import { scrapeApi } from '../../api/scrape.js';
    import { MEDIA_URL } from '../../config.js';
    import { toastError, toastSuccess } from '../../stores/toast.js';
    import { formatDate, parseBBCode } from '../../utils/format.js';

    export let item;
    export let feedId;
    export let paramsSchema = {}; // passed from ItemGrid
    export let onClose;
    export let onUpdate;

    let mouseDownOnBackdrop = false;

    let scraping = false;

    $: supportsScrapeById = 'external_ids' in paramsSchema;

    $: remoteSrc = item.thumbnail_url ?? null;
    $: localSrc = item.thumbnail_path ? `${MEDIA_URL}/${item.thumbnail_path}` : null;
    $: thumbnailSrc = remoteSrc || localSrc;

    $: mediaByType =
        item.media?.reduce((acc, m) => {
            (acc[m.media_type] ??= []).push(m);
            return acc;
        }, {}) ?? {};

    onMount(async () => {
        // Read item when opened
        if (!item.is_read) {
            const updated = { ...item, is_read: true };
            await itemsApi.update(item.id, { is_read: true });
            item = updated;
            onUpdate?.(updated);
        }
    });

    async function scrapeItem() {
        if (scraping) return;
        scraping = true;
        try {
            const job = await itemsApi.scrapeItem(feedId, item.external_id);
            pollScrapeJob(job.id);
        } catch (e) {
            scraping = false;
            console.error('Scrape failed:', e.message);
            toastError(`Scrape failed: ${e.message}`);
        }
    }

    function pollScrapeJob(jobId) {
        const interval = setInterval(async () => {
            try {
                const job = await scrapeApi.getJob(jobId);
                if (job.status === 'done' || job.status === 'error') {
                    clearInterval(interval);
                    scraping = false;
                    if (job.status === 'error') {
                        toastError(`Scrape error: ${job.error_message}`);
                    } else {
                        toastSuccess('Item refreshed');
                        // Reload item from API
                        const updated = await itemsApi.get(item.id);
                        item = updated;
                        onUpdate?.(updated);
                    }
                }
            } catch (e) {
                console.warn(
                    `Error during pollJob for item ${item.id} and job ${jobId}:`,
                    e.message
                );
                clearInterval(interval);
                scraping = false;
            }
        }, 2000);
    }

    async function toggleFavorite() {
        const updated = { ...item, is_favorite: !item.is_favorite };
        await itemsApi.update(item.id, { is_favorite: updated.is_favorite });
        item = updated;
        onUpdate?.(updated);
    }

    async function toggleRead() {
        const updated = { ...item, is_read: !item.is_read };
        await itemsApi.update(item.id, { is_read: updated.is_read });
        item = updated;
        onUpdate?.(updated);
    }

    function handleBackdropKeydown(e) {
        if (e.key === 'Escape') onClose();
    }

    function handleMouseDown(e) {
        mouseDownOnBackdrop = e.target === e.currentTarget;
    }

    function handleBackdropClick(e) {
        if (mouseDownOnBackdrop && e.target === e.currentTarget) onClose();
        mouseDownOnBackdrop = false;
    }

    function handleImgError(e) {
        // If remote failed, fall back to local
        if (thumbnailSrc === remoteSrc && localSrc) {
            thumbnailSrc = localSrc;
        }
    }
</script>

<svelte:window on:keydown={handleBackdropKeydown} />

<div
    class="modal-backdrop"
    on:mousedown={handleMouseDown}
    on:click={handleBackdropClick}
    on:keydown={handleBackdropKeydown}
    role="button"
    tabindex="0"
    aria-label="Close modal"
>
    <div class="modal" role="dialog" aria-modal="true">
        <!-- Header -->
        <div class="modal-header">
            <div class="modal-actions">
                <button
                    class="action-btn"
                    class:active={item.is_favorite}
                    on:click={toggleFavorite}
                    title={item.is_favorite ? 'Remove from favorites' : 'Add to favorites'}
                >
                    {item.is_favorite ? '♥' : '♡'}
                </button>
                <button
                    class="action-btn"
                    on:click={toggleRead}
                    title={item.is_read ? 'Mark as unread' : 'Mark as read'}
                >
                    {item.is_read ? '● read' : '○ unread'}
                </button>
                {#if item.url}
                    <a
                        class="action-btn"
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Open source page"
                    >
                        ↗ source
                    </a>
                {/if}
                {#if supportsScrapeById}
                    <button
                        class="action-btn"
                        class:spinning={scraping}
                        disabled={scraping}
                        on:click={scrapeItem}
                        title={scraping ? 'Refreshing...' : 'Refresh this item'}
                    >
                        ⟳
                    </button>
                {/if}
            </div>
            <button class="close-btn" on:click={onClose} title="Close">✕</button>
        </div>

        <!-- Body -->
        <div class="modal-body">
            <!-- Left column -->
            <div class="col-left">
                {#if thumbnailSrc}
                    <img
                        class="modal-thumbnail"
                        src={thumbnailSrc}
                        alt={item.title}
                        on:error={handleImgError}
                    />
                {/if}

                {#if item.summary}
                    <div class="modal-section">
                        <h4 class="section-title">Summary</h4>
                        <div class="modal-text">{@html parseBBCode(item.summary)}</div>
                    </div>
                {/if}

                {#if item.description && item.description !== item.summary}
                    <div class="modal-section">
                        <h4 class="section-title">Description</h4>
                        <div class="modal-text">{@html parseBBCode(item.description)}</div>
                    </div>
                {/if}
            </div>

            <!-- Right column -->
            <div class="col-right">
                <!-- Title + badges -->
                <div class="modal-title-row">
                    <h2 class="modal-title">{item.title}</h2>
                    <div class="modal-badges">
                        {#if item.is_nsfw}
                            <span class="badge nsfw">NSFW</span>
                        {/if}
                        {#if !item.is_public}
                            <span class="badge unlisted">unlisted</span>
                        {/if}
                    </div>
                </div>

                <!-- Meta dates -->
                <div class="modal-meta">
                    <div class="meta-item">
                        <span class="meta-label">Published</span>
                        <span>{formatDate(item.source_published_at)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Updated</span>
                        <span>{formatDate(item.source_updated_at)}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Scraped</span>
                        <span>{formatDate(item.scraped_at)}</span>
                    </div>
                </div>

                <!-- Author -->
                {#if item.author}
                    <div class="modal-author">
                        {#if item.author.url}
                            <a
                                href={item.author.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                class="author-link"
                            >
                                <span class="author-label">by</span>
                                <span class="author-name">{item.author.name}</span>
                                <span class="author-arrow">↗</span>
                            </a>
                        {:else}
                            <div class="author-link">
                                <span class="author-label">by</span>
                                <span class="author-name">{item.author.name}</span>
                            </div>
                        {/if}
                    </div>
                {/if}

                <!-- Stats -->
                {#if item.stats && Object.keys(item.stats).length > 0}
                    <div class="modal-section stats-section">
                        <h4 class="section-title">Stats</h4>
                        <div class="stats-grid">
                            {#each Object.entries(item.stats) as [key, value]}
                                <div class="stat-item">
                                    <span class="stat-value">{value.toLocaleString()}</span>
                                    <span class="stat-label">{key.replaceAll('_', ' ')}</span>
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Info / meta fields -->
                {#if item.meta && Object.keys(item.meta).length > 0}
                    <div class="modal-section">
                        <h4 class="section-title">Info</h4>
                        <div class="meta-fields">
                            {#each Object.entries(item.meta).sort( ([a], [b]) => a.localeCompare(b) ) as [key, value]}
                                {#if value !== null && value !== undefined}
                                    <div class="meta-field">
                                        <span class="meta-label">{key.replaceAll('_', ' ')}</span>
                                        <span>{value}</span>
                                    </div>
                                {/if}
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Categories -->
                {#if item.categories?.length > 0}
                    <div class="modal-section">
                        <h4 class="section-title">Categories</h4>
                        <div class="tags-list">
                            {#each item.categories as cat}
                                <span class="tag category">{cat.name}</span>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Tags -->
                {#if item.tags?.length > 0}
                    <div class="modal-section">
                        <h4 class="section-title">Tags</h4>
                        <div class="tags-list">
                            {#each item.tags as tag}
                                <span class="tag">{tag}</span>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        </div>

        <!-- Media footer — sticky, full width -->
        {#if item.media?.length > 0}
            <div class="modal-footer">
                {#each Object.entries(mediaByType) as [type, medias]}
                    <div class="footer-section">
                        <h4 class="section-title">{type}s</h4>
                        {#if type === 'image'}
                            <div class="media-images">
                                {#each medias as media}
                                    <a href={media.url} target="_blank" rel="noopener noreferrer">
                                        <img
                                            class="media-image"
                                            src={media.url}
                                            alt={media.label || ''}
                                        />
                                    </a>
                                {/each}
                            </div>
                        {:else}
                            <div class="media-scroll">
                                {#each medias as media}
                                    <a
                                        class="media-chip"
                                        href={media.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                    >
                                        <span class="media-label-text"
                                            >{media.label || media.url}</span
                                        >
                                        <span class="media-arrow">↗</span>
                                    </a>
                                {/each}
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>

<style>
    .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 100;
        padding: 2rem;
        border: none;
        border-radius: 0;
        width: 100%;
        cursor: default;
    }

    .modal {
        background: var(--bg-primary);
        border-radius: var(--radius);
        width: 100%;
        max-width: 1000px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        overflow: hidden;
        cursor: default;
        padding-bottom: 1rem;
    }

    /* Header */
    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border);
        flex-shrink: 0;
    }

    .modal-actions {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .action-btn {
        padding: 0.35rem 0.65rem;
        border-radius: var(--radius);
        font-size: 0.8rem;
        color: var(--text-secondary);
        transition:
            background var(--transition),
            color var(--transition);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        background: none;
        border: none;
        cursor: pointer;
        font-family: inherit;
    }

    .action-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .action-btn.active {
        color: #e8b84b;
    }

    .action-btn.spinning {
        animation: spin 1s linear infinite;
        pointer-events: none;
        color: var(--accent);
    }

    @keyframes spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    .close-btn {
        padding: 0.35rem 0.5rem;
        border-radius: var(--radius);
        color: var(--text-muted);
        font-size: 0.875rem;
        transition:
            background var(--transition),
            color var(--transition);
        background: none;
        border: none;
        cursor: pointer;
        font-family: inherit;
    }

    .close-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    /* Body — two columns */
    .modal-body {
        display: grid;
        grid-template-columns: 4fr 2fr;
        gap: 1.5rem;
        padding: 1.25rem;
        overflow: hidden;
        min-height: 0;
        flex: 1;
    }

    .col-left,
    .col-right {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        min-width: 0;
        overflow-y: auto;
        overflow-x: hidden;
    }

    .col-left {
        padding-right: 0.5rem;
    }

    .col-right {
        padding-right: 0.25rem;
    }

    .modal-thumbnail {
        width: 100%;
        aspect-ratio: 16 / 9;
        object-fit: contain;
        border-radius: var(--radius);
        background: var(--bg-tertiary); /* fills empty space around image */
    }

    /* Title */
    .modal-title-row {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
    }

    .modal-title {
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.3;
        flex: 1;
    }

    .modal-badges {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        flex-shrink: 0;
    }

    .badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 0.15rem 0.35rem;
        border-radius: 4px;
        text-transform: uppercase;
        text-align: center;
    }

    .badge.nsfw {
        background: var(--danger);
        color: white;
    }
    .badge.unlisted {
        background: var(--text-muted);
        color: white;
    }

    /* Meta */
    .modal-meta {
        justify-content: space-around;
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem 1.25rem;
    }

    .meta-item {
        align-items: center;
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
        font-size: 0.875rem;
    }

    .meta-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
    }

    /* Author */
    .modal-author {
        margin-top: -0.5rem;
    }

    .author-link {
        width: 100%;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.65rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        font-size: 0.875rem;
        text-decoration: none;
        color: var(--text-primary);
        transition:
            background var(--transition),
            border-color var(--transition);
    }

    .author-link:hover {
        background: var(--bg-tertiary);
        border-color: var(--accent);
    }

    .author-label {
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    .author-name {
        font-weight: 500;
        color: var(--accent);
    }

    .author-arrow {
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    /* Sections */
    .modal-section {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .section-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        font-weight: 600;
    }

    /* Stats */
    .stats-section .section-title {
        text-align: center;
    }

    .stats-grid {
        justify-content: space-evenly;
        display: flex;
        gap: 1.25rem;
        flex-wrap: wrap;
    }

    .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.1rem;
        max-width: 80px;
    }

    .stat-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: capitalize;
        text-align: center;
        word-break: break-word;
        line-height: 1.3;
    }

    /* Meta fields */
    .meta-fields {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    .meta-field {
        display: flex;
        gap: 0.75rem;
        font-size: 0.875rem;
        align-items: baseline;
    }

    .meta-field .meta-label {
        min-width: 100px;
        flex-shrink: 0;
        text-transform: capitalize;
    }

    /* Tags / Categories */
    .tags-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
    }

    .tag {
        font-size: 0.75rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        background: var(--bg-tertiary);
        color: var(--text-secondary);
    }

    .tag.category {
        background: var(--bg-tertiary);
        border: 1px solid var(--border);
        color: var(--text-primary);
    }

    /* Text content */
    .modal-text {
        font-size: 0.875rem;
        line-height: 1.6;
        color: var(--text-secondary);
    }

    .modal-text :global(a) {
        color: var(--accent);
    }

    .modal-text :global(img) {
        max-width: 100%;
        height: auto;
        border-radius: var(--radius);
    }

    /* Media links/files */
    .modal-footer {
        flex-shrink: 0;
        border-top: 1px solid var(--border);
        padding: 0.75rem 1.25rem;
        background: var(--bg-primary);
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .footer-section {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .media-scroll {
        display: flex;
        flex-direction: row;
        gap: 0.5rem;
        overflow-x: auto;
        padding-bottom: 0.25rem;
        scrollbar-width: thin;
        min-width: 0;
    }

    .media-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.65rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        font-size: 0.8rem;
        text-decoration: none;
        white-space: nowrap;
        flex-shrink: 0;
        color: var(--text-primary);
        transition:
            background var(--transition),
            border-color var(--transition);
    }

    .media-chip:hover {
        background: var(--bg-tertiary);
        border-color: var(--accent);
    }

    .media-chip .media-label-text {
        color: var(--accent);
    }

    .media-chip .media-arrow {
        color: var(--text-muted);
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    .media-arrow {
        color: var(--text-muted);
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    .media-images {
        display: flex;
        flex-direction: row;
        gap: 0.5rem;
        overflow-x: auto;
        padding-bottom: 0.25rem;
        scrollbar-width: thin;
        min-width: 0;
        max-width: 100%;
    }

    .media-image {
        height: 80px;
        width: 120px;
        border-radius: var(--radius);
        object-fit: cover;
        flex-shrink: 0;
        cursor: pointer;
        transition: opacity var(--transition);
    }
</style>
