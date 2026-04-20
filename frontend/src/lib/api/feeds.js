import { api } from './client.js';

export const feedsApi = {
    list: (sourceId, params = {}) => {
        const query = new URLSearchParams({
            source_id: sourceId,
            limit: 200,
            ...params,
        });
        return api.get(`/feeds/?${query}`);
    },
    get: (id) => api.get(`/feeds/${id}`),
    create: (data) => api.post('/feeds/', data),
    update: (id, data) => api.patch(`/feeds/${id}`, data),
    delete: (id) => api.delete(`/feeds/${id}`),
};