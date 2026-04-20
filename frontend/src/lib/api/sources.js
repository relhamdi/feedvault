import { api } from './client.js';

export const sourcesApi = {
    list: (params = {}) => {
        const query = new URLSearchParams({
            limit: 200,
            ...params,
        });
        return api.get(`/sources/?${query}`);
    },
    get: (id) => api.get(`/sources/${id}`),
    create: (data) => api.post('/sources/', data),
    update: (id, data) => api.patch(`/sources/${id}`, data),
    delete: (id) => api.delete(`/sources/${id}`),
    bootstrap: (slug) => api.post(`/sources/bootstrap/${slug}`),
    bootstrapAll: () => api.post('/sources/bootstrap'),
};