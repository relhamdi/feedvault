<script>
    import { feedsApi } from '../../api/feeds.js';
    import { sourcesApi } from '../../api/sources.js';
    import { toastError } from '../../stores/toast.js';
    import { parseTags } from '../../utils/format.js';
    import FormModal from '../modals/FormModal.svelte';
    import FormField from '../ui/FormField.svelte';
    import ToggleField from '../ui/ToggleField.svelte';

    export let feed = null; // null = create mode
    export let source;
    export let onClose;
    export let onSaved;

    let paramsSchema = {};
    let paramsValues = {};
    let loading = false;
    let error = null;

    $: isEdit = feed !== null;
    $: if (source?.slug) fetchParamsSchema(source.slug);

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

    function validateParams() {
        try {
            JSON.parse(form.params);
            paramsError = null;
            return true;
        } catch (e) {
            paramsError = 'Invalid JSON.';
            toastError('Invalid JSON');
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
                params:
                    Object.keys(paramsSchema).length > 0 ? buildParams() : JSON.parse(form.params),

                source_id: source.id,
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
            toastError('Incorrect form');
        } finally {
            loading = false;
        }
    }

    async function fetchParamsSchema(slug) {
        try {
            paramsSchema = await sourcesApi.paramsSchema(slug);
            if (!isEdit) {
                // Initialize empty values, external_ids as array
                paramsValues = Object.fromEntries(
                    Object.keys(paramsSchema).map((k) => [k, k === 'external_ids' ? '' : ''])
                );
            } else {
                // Pre-fill from existing feed.params
                paramsValues = Object.fromEntries(
                    Object.keys(paramsSchema).map((k) => {
                        const val = feed?.params?.[k];
                        if (k === 'external_ids' && Array.isArray(val)) {
                            return [k, val.join(', ')];
                        }
                        return [k, val ?? ''];
                    })
                );
            }
        } catch (e) {
            console.warn(`Failed to load paramsSchema for slug '${slug}':`, e.message);
            paramsSchema = {};
            paramsValues = {};
        }
    }

    function buildParams() {
        const result = {};
        for (const [key, value] of Object.entries(paramsValues)) {
            if (!value && value !== 0) continue;
            if (key === 'external_ids') {
                const ids = String(value)
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean);
                if (ids.length > 0) result[key] = ids;
            } else {
                // Try to cast to number if possible
                const num = Number(value);
                result[key] = isNaN(num) || value === '' ? value : num;
            }
        }
        return result;
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
        <p class="global-form-error">{error}</p>
    {/if}

    <FormField id="feed-name" label="Name" required>
        <input id="feed-name" type="text" bind:value={form.name} placeholder="Name of the feed" />
    </FormField>

    <FormField id="feed-url" label="URL" required hint="Display URL for this feed.">
        <input id="feed-url" type="url" bind:value={form.url} placeholder="https://..." />
    </FormField>

    <div class="global-form-row">
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

    {#if Object.keys(paramsSchema).length > 0}
        <div class="global-schema-section">
            <p class="global-schema-section-title">Params</p>
            {#each Object.entries(paramsSchema) as [key, hint]}
                <FormField id="param-{key}" label={key} hint={String(hint)}>
                    {#if key === 'external_ids'}
                        <textarea
                            id="param-{key}"
                            bind:value={paramsValues[key]}
                            rows="2"
                            placeholder="Coma separated IDs..."
                            spellcheck="false"
                        ></textarea>
                    {:else}
                        <input
                            id="param-{key}"
                            type="text"
                            bind:value={paramsValues[key]}
                            placeholder={String(hint)}
                        />
                    {/if}
                </FormField>
            {/each}
        </div>
    {:else}
        <FormField
            id="feed-params"
            label="Params"
            hint="JSON config for the scraper"
            error={paramsError}
        >
            <textarea
                id="feed-params"
                bind:value={form.params}
                on:blur={validateParams}
                rows="4"
                spellcheck="false"
            ></textarea>
        </FormField>
    {/if}

    <ToggleField id="source-active" label="Active" bind:checked={form.is_active} />
</FormModal>
