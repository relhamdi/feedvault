<script>
    import { onMount } from "svelte";
    import Sidebar from "./lib/components/sidebar/Sidebar.svelte";
    import { theme } from "./lib/stores/theme.js";

    onMount(() => {
        document.documentElement.setAttribute("data-theme", $theme);
    });
</script>

<div class="app-layout">
    <aside class="sidebar-slot">
        <Sidebar />
    </aside>

    <main class="main-slot">
        <!-- Main content here -->
        <p style="color: var(--text-secondary); padding: 1rem;">Contenu</p>
    </main>
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
</style>
