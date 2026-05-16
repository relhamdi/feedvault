<script>
    export let label;
    export let id;
    export let required = false;
    export let hint = null;
    export let error = null;
</script>

<div class="field">
    <label class="form-field-label" for={id}>
        {label}
        {#if required}<span class="required">*</span>{/if}
    </label>
    <slot />
    {#if hint && !error}
        <span class="form-field-hint">{hint}</span>
    {/if}
    {#if error}
        <span class="field-error">{error}</span>
    {/if}
</div>

<style>
    .field {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .required {
        color: var(--danger);
        margin-left: 0.2rem;
    }

    .field-error {
        font-size: 0.75rem;
        color: var(--danger);
    }
</style>
