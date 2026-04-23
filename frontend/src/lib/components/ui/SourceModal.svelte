<script>
    import { onMount } from 'svelte';
    import { sourcesApi } from '../../api/sources.js';
    import FormField from '../ui/FormField.svelte';
    import FormModal from '../ui/FormModal.svelte';

    export let source = null; // null = create mode
    export let onClose;
    export let onSaved;

    const SOURCE_TYPES = ['RSS', 'API', 'SCRAPER'];

    let loading = false;
    let error = null;
    let credentialsSchema = {};
    let credentialsValues = {};

    let slugDebounceTimer = null;

    let form = {
        slug: source?.slug ?? '',
        name: source?.name ?? '',
        source_type: source?.source_type ?? 'API',
        base_url: source?.base_url ?? '',
        color: source?.color ?? '',
        icon_path: source?.icon_path ?? '',
        default_tags: source?.default_tags?.join(', ') ?? '',
        is_active: source?.is_active ?? true,
    };

    $: isEdit = source !== null;

    // Fetch credentials schema when slug changes (on create)
    $: if (!isEdit && form.slug) {
        clearTimeout(slugDebounceTimer);
        slugDebounceTimer = setTimeout(() => fetchCredentialsSchema(form.slug), 500);
    }

    onMount(async () => {
        // Fetch credentials schema (on edit)
        if (isEdit && source?.slug) {
            await fetchCredentialsSchema(source.slug);
        }
    });

    async function fetchCredentialsSchema(slug) {
        try {
            credentialsSchema = await sourcesApi.credentialsSchema(slug);
            // Initialize empty values for each key
            credentialsValues = Object.fromEntries(
                Object.keys(credentialsSchema).map((k) => [k, ''])
            );
        } catch (_) {
            credentialsSchema = {};
            credentialsValues = {};
        }
    }

    function parseTags(str) {
        return str
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean);
    }

    async function handleSubmit() {
        if (!form.name || !form.slug || !form.base_url) {
            error = 'Name, slug and base URL are required.';
            return;
        }
        loading = true;
        error = null;
        try {
            const payload = {
                ...form,
                default_tags: parseTags(form.default_tags),
                icon_path: form.icon_path || null,
                color: form.color || null,
            };

            let saved;
            if (isEdit) {
                saved = await sourcesApi.update(source.id, payload);
            } else {
                saved = await sourcesApi.create(payload);
                // Save credentials if any filled
                const filledCredentials = Object.fromEntries(
                    Object.entries(credentialsValues).filter(([_, v]) => v !== '')
                );
                if (Object.keys(filledCredentials).length > 0) {
                    await sourcesApi.updateCredentials(saved.id, filledCredentials);
                }
            }
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
    title={isEdit ? `Edit — ${source.name}` : 'Add source'}
    {onClose}
    onSubmit={handleSubmit}
    submitLabel={isEdit ? 'Save' : 'Create'}
    {loading}
>
    {#if error}
        <p class="form-error">{error}</p>
    {/if}

    <FormField id="source-name" label="Name" required>
        <input id="source-name" type="text" bind:value={form.name} placeholder="Source Name" />
    </FormField>

    <FormField
        id="source-slug"
        label="Slug"
        required
        hint={isEdit ? 'Slug cannot be changed after creation.' : 'Unique identifier.'}
    >
        <input
            id="source-slug"
            type="text"
            bind:value={form.slug}
            placeholder="source_slug"
            disabled={isEdit}
        />
    </FormField>

    <FormField id="source-type" label="Source type" required>
        <select id="source-type" bind:value={form.source_type}>
            {#each SOURCE_TYPES as type}
                <option value={type}>{type}</option>
            {/each}
        </select>
    </FormField>

    <FormField id="source-url" label="Base URL" required>
        <input id="source-url" type="url" bind:value={form.base_url} placeholder="https://.../v1" />
    </FormField>

    <div class="row">
        <FormField id="source-color" label="Color">
            <input id="source-color" type="color" bind:value={form.color} />
        </FormField>
        <FormField id="source-icon" label="Icon URL">
            <input
                id="source-icon"
                type="url"
                bind:value={form.icon_path}
                placeholder="https://..."
            />
        </FormField>
    </div>

    <FormField id="source-tags" label="Default tags" hint="Comma-separated.">
        <input
            id="source-tags"
            type="text"
            bind:value={form.default_tags}
            placeholder="tag1, tag2, ..."
        />
    </FormField>

    <div class="toggle-row">
        <label for="source-active" class="toggle-label">Active</label>
        <input id="source-active" type="checkbox" bind:checked={form.is_active} />
    </div>

    <!-- Credentials — create mode only, shown if schema available -->
    {#if !isEdit && Object.keys(credentialsSchema).length > 0}
        <div class="credentials-section">
            <p class="section-title">Credentials</p>
            {#each Object.entries(credentialsSchema) as [key, hint]}
                <FormField id="cred-{key}" label={key} hint={String(hint)}>
                    <input
                        id="cred-{key}"
                        type="password"
                        bind:value={credentialsValues[key]}
                        placeholder={String(hint)}
                    />
                </FormField>
            {/each}
        </div>
    {/if}

    <!-- Credentials — edit mode -->
    {#if isEdit}
        <div class="credentials-section">
            <p class="section-title">Credentials</p>
            <p class="section-hint">
                To update credentials, enter new values below. Leave empty to keep existing.
            </p>
            {#each Object.entries(credentialsValues) as [key, _]}
                <FormField id="cred-{key}" label={key}>
                    <input id="cred-{key}" type="password" bind:value={credentialsValues[key]} />
                </FormField>
            {/each}
            {#if Object.keys(credentialsValues).length === 0}
                <p class="section-hint">No credentials schema available for this source.</p>
            {/if}
        </div>
    {/if}
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

    .credentials-section {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        padding: 0.75rem;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--bg-secondary);
    }

    .section-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
    }

    .section-hint {
        font-size: 0.75rem;
        color: var(--text-muted);
    }
</style>
