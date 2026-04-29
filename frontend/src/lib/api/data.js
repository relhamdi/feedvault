import { api } from './client.js';

export const dataApi = {
    /**
     * Trigger a file download via a Blob, and return the filename used.
     */
    async exportData(selection = {}, options = {}) {
        const body = {
            selection: {
                feed_ids: selection.feed_ids ?? [],
                collection_ids: selection.collection_ids ?? [],
            },
            options: {
                include_credentials: options.includeCredentials ?? false,
                include_read_status: options.includeReadStatus ?? true,
                include_favorites: options.includeFavorites ?? true,
                include_collections: options.includeCollections ?? true,
            },
        };

        const response = await api.download('/data/export', body);

        // Extract filename from Content-Disposition header
        const disposition = response.headers.get('Content-Disposition') ?? '';
        const filename = disposition.split('filename=')[1]?.trim() ?? 'feedvault_export.json';

        // Trigger browser download via blob URL
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        return filename;
    },

    /**
     * Upload a file through FormData.
     */
    async importData(file, params = {}) {
        const query = new URLSearchParams({
            conflict_strategy: params.conflictStrategy ?? 'upsert',
            redownload_missing_images: params.redownloadMissingImages ?? false,
        });
        const formData = new FormData();
        formData.append('file', file);
        return api.upload(`/data/import?${query}`, formData);
    },

    // Reset database
    resetDatabase: () => api.delete('/data/reset'),
};
