<script>
    import { collectionsApi } from '../../api/collections.js';
    import { feedsApi } from '../../api/feeds.js';
    import { sourcesApi } from '../../api/sources.js';
    import { toastError } from '../../stores/toast.js';
    import FormModal from '../modals/FormModal.svelte';
    import FormField from '../ui/FormField.svelte';
    import MultiSelect from '../ui/MultiSelect.svelte';

    export let collection = null; // null = create mode
    export let onClose;
    export let onSaved;

    $: isEdit = collection !== null;

    let loading = false;
    let error = null;

    // Sources + feeds for filter selectors
    let sources = [];
    let feeds = [];
    let loadingOptions = true;

    let form = {
        name: collection?.name ?? '',
        color: collection?.color ?? '',
        filter_source_ids: collection?.filter_source_ids ?? [],
        filter_feed_ids: collection?.filter_feed_ids ?? [],
        filter_tags: collection?.filter_tags?.join(', ') ?? '',
        filter_operator: collection?.filter_operator ?? 'OR',
    };

    // Load sources + feeds for the multiselects
    async function loadOptions() {
        loadingOptions = true;
        try {
            const [sourcesRes, feedsRes] = await Promise.all([
                sourcesApi.list({ limit: 200 }),
                feedsApi.listAll({ limit: 200 }),
            ]);
            sources = sourcesRes.items;
            feeds = feedsRes.items;
        } catch (e) {
            toastError('Failed to load sources/feeds');
        } finally {
            loadingOptions = false;
        }
    }

    loadOptions();

    $: sourceOptions = sources.map((s) => ({ value: s.id, label: s.name }));
    $: feedOptions = feeds.map((f) => {
        const source = sources.find((s) => s.id === f.source_id);
        return { value: f.id, label: source ? `[${source.name}] ${f.name}` : f.name };
    });

    async function handleSubmit() {
        if (!form.name) {
            error = 'Name is required.';
            return;
        }

        loading = true;
        error = null;

        try {
            const tags = form.filter_tags
                .split(',')
                .map((t) => t.trim())
                .filter(Boolean);

            const payload = {
                name: form.name,
                color: form.color || null,
                filter_source_ids: form.filter_source_ids.length ? form.filter_source_ids : null,
                filter_feed_ids: form.filter_feed_ids.length ? form.filter_feed_ids : null,
                filter_tags: tags.length ? tags : null,
                filter_operator: form.filter_operator,
            };

            const saved = isEdit
                ? await collectionsApi.update(collection.id, payload)
                : await collectionsApi.create(payload);

            onSaved(saved);
            onClose();
        } catch (e) {
            error = e.message;
            toastError('Failed to save collection');
        } finally {
            loading = false;
        }
    }
</script>

<FormModal
    title={isEdit ? `Edit — ${collection.name}` : 'New collection'}
    {onClose}
    onSubmit={handleSubmit}
    submitLabel={isEdit ? 'Save' : 'Create'}
    {loading}
>
    {#if error}
        <p class="form-error">{error}</p>
    {/if}

    {#if loading}
        <p class="hint">Loading...</p>
    {:else}
        <div class="form-row">
            <FormField id="col-color" label="Color">
                <input id="col-color" type="color" bind:value={form.color} />
            </FormField>
            <FormField id="col-name" label="Name" required style="flex:1">
                <input
                    id="col-name"
                    type="text"
                    bind:value={form.name}
                    placeholder="Collection name"
                />
            </FormField>
        </div>

        <FormField id="col-operator" label="Combine filters with">
            <div class="inline-row">
                <span class="hint">Item matches any filter —</span>
                <div class="operator-toggle">
                    <button
                        class="operator-btn"
                        class:active={form.filter_operator === 'OR'}
                        on:click={() => (form.filter_operator = 'OR')}
                        type="button">OR</button
                    >
                    <button
                        class="operator-btn"
                        class:active={form.filter_operator === 'AND'}
                        on:click={() => (form.filter_operator = 'AND')}
                        type="button">AND</button
                    >
                </div>
                <span class="hint">— Item matches all filters</span>
            </div>
        </FormField>

        <div class="form-row">
            <FormField
                id="col-sources"
                label="Filter by sources"
                hint="Items from any of these sources."
            >
                {#if loadingOptions}
                    <span class="hint">Loading...</span>
                {:else}
                    <MultiSelect
                        id="col-sources"
                        options={sourceOptions}
                        bind:selected={form.filter_source_ids}
                        placeholder="All sources"
                    />
                {/if}
            </FormField>

            <FormField id="col-feeds" label="Filter by feeds" hint="Items from any of these feeds.">
                {#if loadingOptions}
                    <span class="hint">Loading...</span>
                {:else}
                    <MultiSelect
                        id="col-feeds"
                        options={feedOptions}
                        bind:selected={form.filter_feed_ids}
                        placeholder="All feeds"
                    />
                {/if}
            </FormField>
        </div>

        <FormField
            id="col-tags"
            label="Filter by tags"
            hint="Comma-separated. Items must have at least one."
        >
            <input
                id="col-tags"
                type="text"
                bind:value={form.filter_tags}
                placeholder="tag1, tag2, ..."
            />
        </FormField>
    {/if}
</FormModal>

<style>
    .inline-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    .hint {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .operator-toggle {
        display: flex;
        gap: 0;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        width: fit-content;
    }

    .operator-btn {
        padding: 0.35rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-muted);
        transition:
            background var(--transition),
            color var(--transition);
    }

    .operator-btn:first-child {
        border-right: 1px solid var(--border);
    }

    .operator-btn.active {
        background: var(--accent);
        color: white;
    }

    .operator-btn:hover:not(.active) {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }
</style>
