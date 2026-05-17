<script>
    import { activeContextMenuId } from '../../stores/ui.js';

    export let x = 0;
    export let y = 0;
    export let items = []; // { label, action, danger? }
    export let onClose;

    let openSubmenuIndex = null;
    let submenuPos = { x: 0, y: 0 };

    function handleClick(action) {
        action();
        onClose();
    }

    function handleKeydown(e) {
        if (e.key === 'Escape') onClose();
    }

    function handleOutsideClick() {
        activeContextMenuId.set(null);
        onClose();
    }

    function handleItemEnter(e, index, item) {
        if (!item.children) {
            openSubmenuIndex = null;
            return;
        }

        openSubmenuIndex = index;
        const rect = e.currentTarget.getBoundingClientRect();
        const submenuWidth = 160;
        const wouldOverflow = rect.right + submenuWidth > window.innerWidth;
        submenuPos = {
            x: wouldOverflow ? rect.left - submenuWidth : rect.right,
            y: rect.top,
        };
    }
</script>

<svelte:window on:keydown={handleKeydown} on:click={handleOutsideClick} />

<menu
    class="context-menu"
    style="left: {x}px; top: {y}px"
    on:click|stopPropagation
    on:keydown|stopPropagation
    role="menu"
>
    {#each items as item, i}
        {#if item.separator}
            <li class="separator" role="separator"></li>
        {:else}
            <li class="item-wrapper">
                <button
                    class="context-item"
                    class:danger={item.danger}
                    class:disabled={item.disabled}
                    class:has-children={item.children}
                    disabled={item.disabled}
                    on:mouseenter={(e) => handleItemEnter(e, i, item)}
                    on:click={() => !item.disabled && handleClick(item.action)}
                >
                    {#if item.icon}
                        <span class="context-icon">{item.icon}</span>
                    {/if}
                    {item.label}
                    {#if item.children}<span class="submenu-arrow">›</span>{/if}
                </button>

                {#if item.children && openSubmenuIndex === i}
                    <menu
                        class="context-menu submenu"
                        style="left: {submenuPos.x}px; top: {submenuPos.y}px"
                        on:click|stopPropagation
                        on:keydown|stopPropagation
                        role="menu"
                    >
                        {#each item.children as child}
                            <li>
                                <button
                                    class="context-item"
                                    on:click={() => handleClick(child.action)}
                                >
                                    {#if child.icon}<span class="context-icon">{child.icon}</span
                                        >{/if}
                                    {child.label}
                                </button>
                            </li>
                        {/each}
                    </menu>
                {/if}
            </li>
        {/if}
    {/each}
</menu>

<style>
    .item-wrapper {
        position: relative;
    }

    .context-menu {
        position: fixed;
        z-index: 200;
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        padding: 0.25rem;
        min-width: 160px;
        list-style: none;
    }

    .context-item {
        width: 100%;
        text-align: left;
        padding: 0.4rem 0.65rem;
        border-radius: calc(var(--radius) - 2px);
        font-size: 0.875rem;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: background var(--transition);
    }

    .context-item:hover {
        background: var(--bg-tertiary);
    }

    .context-item.danger {
        color: var(--danger);
    }

    .context-item.danger:hover {
        background: color-mix(in srgb, var(--danger) 10%, transparent);
    }

    .context-item.disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .context-item.disabled:hover {
        background: none;
    }

    .context-icon {
        font-size: 0.8rem;
        width: 16px;
        text-align: center;
    }

    .separator {
        height: 1px;
        background: var(--border);
        margin: 0.25rem 0;
    }

    .item-wrapper {
        position: relative;
    }

    .has-children {
        justify-content: space-between;
    }

    .submenu-arrow {
        margin-left: auto;
        color: var(--text-muted);
        font-size: 0.8rem;
    }

    .submenu {
        position: fixed;
        z-index: 201;
    }
</style>
