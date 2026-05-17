<script>
    import { feedsApi } from '../../api/feeds.js';
    import { sourcesApi } from '../../api/sources.js';
    import { toastError, toastWarning } from '../../stores/toast.js';
    import { parseComaString } from '../../utils/format.js';
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
                default_tags: parseComaString(form.default_tags),
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
            paramsValues = Object.fromEntries(
                Object.entries(paramsSchema).map(([k, field]) => {
                    if (isEdit) {
                        const val = feed?.params?.[k];
                        if (field.type === 'textarea' && Array.isArray(val))
                            return [k, val.join(', ')];
                        return [k, val ?? field.default ?? ''];
                    }
                    return [k, field.default ?? ''];
                })
            );
        } catch (e) {
            console.warn(`Failed to load paramsSchema for slug '${slug}':`, e.message);
            paramsSchema = {};
            paramsValues = {};
        }
    }

    function buildParams() {
        const result = {};
        for (const [key, value] of Object.entries(paramsValues)) {
            // Skip only null/undefined/empty string, not false or 0
            if (value === null || value === undefined || value === '') continue;
            const field = paramsSchema[key];
            if (field?.type === 'bool') {
                result[key] = Boolean(value);
            } else if (field?.type === 'textarea') {
                const ids = parseComaString(String(value));
                if (ids.length > 0) result[key] = ids;
            } else if (field?.type === 'number') {
                const num = Number(value);
                // Ignore invalid values
                if (isNaN(num)) continue;
                result[key] = num;
            } else {
                result[key] = value;
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
            {#each Object.entries(paramsSchema) as [key, field]}
                {#if field.type === 'bool'}
                    <ToggleField
                        id="param-{key}"
                        label={key}
                        bind:checked={paramsValues[key]}
                        hint={field.description}
                    />
                {:else}
                    <FormField id="param-{key}" label={key} hint={field.description}>
                        {#if field.type === 'select'}
                            <select id="param-{key}" bind:value={paramsValues[key]}>
                                {#each field.options as opt}
                                    <option value={opt.value}>{opt.label}</option>
                                {/each}
                            </select>
                        {:else if field.type === 'number'}
                            <input
                                id="param-{key}"
                                type="number"
                                bind:value={paramsValues[key]}
                                min={field.min ?? ''}
                                max={field.max ?? ''}
                                placeholder={String(field.default ?? '')}
                            />
                        {:else if field.type === 'textarea'}
                            <textarea
                                id="param-{key}"
                                bind:value={paramsValues[key]}
                                rows="2"
                                placeholder="Comma separated values..."
                                spellcheck="false"
                            ></textarea>
                        {:else if field.type === 'bool'}
                            <ToggleField
                                id="param-{key}"
                                label=""
                                bind:checked={paramsValues[key]}
                            />
                        {:else}
                            <input
                                id="param-{key}"
                                type="text"
                                bind:value={paramsValues[key]}
                                placeholder={field.description}
                            />
                        {/if}
                    </FormField>
                {/if}
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
