<script>
    import { feedsApi } from '../../api/feeds.js';
    import FormField from './FormField.svelte';
    import FormModal from './FormModal.svelte';

    const paramsHint = 'JSON config for the scraper, e.g. {"game_id": 11534}';

    export let feed = null; // null = create mode
    export let sourceId; // pre-filled from selected source
    export let onClose;
    export let onSaved;

    let loading = false;
    let error = null;

    $: isEdit = feed !== null;

    let form = {
        name: feed?.name ?? '',
        url: feed?.url ?? '',
        color: feed?.color ?? '',
        icon_path: feed?.icon_path ?? '',
        default_tags: feed?.default_tags?.join(', ') ?? '',
        is_active: feed?.is_active ?? true,
        params: feed?.params ? JSON.stringify(feed.params, null, 2) : '{}',
    };

    let paramsError = null;

    function parseTags(str) {
        return str
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean);
    }

    function validateParams() {
        try {
            JSON.parse(form.params);
            paramsError = null;
            return true;
        } catch (_) {
            paramsError = 'Invalid JSON.';
            return false;
        }
    }

    async function handleSubmit() {
        if (!form.name || !form.url) {
            error = 'Name and URL are required.';
            return;
        }
        if (!validateParams()) return;

        loading = true;
        error = null;
        try {
            const payload = {
                name: form.name,
                url: form.url,
                color: form.color || null,
                icon_path: form.icon_path || null,
                default_tags: parseTags(form.default_tags),
                is_active: form.is_active,
                params: JSON.parse(form.params),
                source_id: sourceId,
            };

            const response = isEdit
                ? await feedsApi.update(feed.id, payload)
                : await feedsApi.create(payload);

            const saved = isEdit ? response : response.feed;
            if (response.warning) toastWarning(response.warning);

            onSaved(saved);
            onClose();
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }
</script>

<FormModal
    title={isEdit ? `Edit — ${feed.name}` : 'Add feed'}
    {onClose}
    onSubmit={handleSubmit}
    submitLabel={isEdit ? 'Save' : 'Create'}
    {loading}
>
    {#if error}
        <p class="form-error">{error}</p>
    {/if}

    <FormField id="feed-name" label="Name" required>
        <input id="feed-name" type="text" bind:value={form.name} placeholder="Name of the feed" />
    </FormField>

    <FormField id="feed-url" label="URL" required hint="Display URL for this feed.">
        <input id="feed-url" type="url" bind:value={form.url} placeholder="https://..." />
    </FormField>

    <div class="row">
        <FormField id="feed-color" label="Color">
            <input id="feed-color" type="color" bind:value={form.color} />
        </FormField>
        <FormField id="feed-icon" label="Icon URL">
            <input
                id="feed-icon"
                type="url"
                bind:value={form.icon_path}
                placeholder="https://..."
            />
        </FormField>
    </div>

    <FormField id="feed-tags" label="Default tags" hint="Comma-separated.">
        <input
            id="feed-tags"
            type="text"
            bind:value={form.default_tags}
            placeholder="tag1, tag2, ..."
        />
    </FormField>

    <FormField id="feed-params" label="Params" hint={paramsHint} error={paramsError}>
        <textarea
            id="feed-params"
            bind:value={form.params}
            on:blur={validateParams}
            rows="4"
            spellcheck="false"
        ></textarea>
    </FormField>

    <div class="toggle-row">
        <label for="feed-active" class="toggle-label">Active</label>
        <input id="feed-active" type="checkbox" bind:checked={form.is_active} />
    </div>
</FormModal>

<style>
    .form-error {
        font-size: 0.875rem;
        color: var(--danger);
        padding: 0.5rem 0.75rem;
        background: color-mix(in srgb, var(--danger) 10%, transparent);
        border-radius: var(--radius);
    }

    .row {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 0.75rem;
        align-items: end;
    }

    .toggle-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .toggle-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-secondary);
    }
</style>
