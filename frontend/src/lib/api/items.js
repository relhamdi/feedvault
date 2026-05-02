import { DEFAULT_ITEMS_LIMIT } from '../config.js';
import { api } from './client.js';

export const itemsApi = {
    list: (feedId, params = {}) => {
        const query = new URLSearchParams({
            feed_id: feedId,
            limit: DEFAULT_ITEMS_LIMIT,
            ...params,
        });
        return api.get(`/items/?${query}`);
    },
    get: (id) => api.get(`/items/${id}`),
    update: (id, data) => api.patch(`/items/${id}`, data),
    scrape: (data) => api.post('/scrape/', data),
    scrapeItem: (feedId, externalId) =>
        api.post('/scrape/', {
            feed_id: feedId,
            mode: 'FULL',
            external_ids: [externalId],
        }),
};
