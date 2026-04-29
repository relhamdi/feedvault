import { api } from './client.js';

const DEFAULT_FEED_LIMIT = 200;

export const feedsApi = {
    list: (sourceId, params = {}) => {
        const query = new URLSearchParams({
            source_id: sourceId,
            limit: DEFAULT_FEED_LIMIT,
            ...params,
        });
        return api.get(`/feeds/?${query}`);
    },
    listAll: (params = {}) => {
        const query = new URLSearchParams({ limit: DEFAULT_FEED_LIMIT, ...params });
        return api.get(`/feeds/?${query}`);
    },
    get: (id) => api.get(`/feeds/${id}`),
    create: (data) => api.post('/feeds/', data),
    update: (id, data) => api.patch(`/feeds/${id}`, data),
    delete: (id) => api.delete(`/feeds/${id}`),
};
