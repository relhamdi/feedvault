import { DEFAULT_ITEMS_LIMIT } from '../config.js';
import { api } from './client.js';

export const collectionsApi = {
    list: (params = {}) => {
        const query = new URLSearchParams({ limit: 200, ...params });
        return api.get(`/collections/?${query}`);
    },
    get: (id) => api.get(`/collections/${id}`),
    create: (data) => api.post('/collections/', data),
    update: (id, data) => api.patch(`/collections/${id}`, data),
    delete: (id) => api.delete(`/collections/${id}`),
    items: (id, params = {}) => {
        const query = new URLSearchParams({ limit: DEFAULT_ITEMS_LIMIT, ...params });
        return api.get(`/collections/${id}/items?${query}`);
    },
};
