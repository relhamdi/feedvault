<script>
    import { onMount } from 'svelte';
    import CollectionItemGrid from './lib/components/collection/CollectionItemGrid.svelte';
    import CollectionTabs from './lib/components/collection/CollectionTabs.svelte';
    import FeedTabs from './lib/components/feed/FeedTabs.svelte';
    import ItemGrid from './lib/components/item/ItemGrid.svelte';
    import Sidebar from './lib/components/sidebar/Sidebar.svelte';
    import ToastContainer from './lib/components/ui/ToastContainer.svelte';
    import { collectionsMode } from './lib/stores/navigation.js';
    import { theme } from './lib/stores/theme.js';

    onMount(() => {
        document.documentElement.setAttribute('data-theme', $theme);
    });
</script>

<div class="app-layout">
    <aside class="sidebar-slot">
        <Sidebar />
    </aside>

    <main class="main-slot">
        {#if $collectionsMode}
            <CollectionTabs />
        {:else}
            <FeedTabs />
        {/if}
        <div class="content-slot">
            {#if $collectionsMode}
                <CollectionItemGrid />
            {:else}
                <ItemGrid />
            {/if}
        </div>
    </main>

    <ToastContainer />
</div>

<style>
    .app-layout {
        display: flex;
        height: 100vh;
        overflow: hidden;
    }

    .sidebar-slot {
        width: var(--sidebar-width);
        min-width: var(--sidebar-width);
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
        overflow-y: auto;
    }

    .main-slot {
        flex: 1;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }

    .content-slot {
        flex: 1;
        overflow-y: auto;
    }
</style>
