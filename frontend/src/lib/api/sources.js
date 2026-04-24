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
    updateCredentials: (id, data) => api.put(`/sources/${id}/credentials`, data),
    registeredSlugs: () => api.get('/sources/registered-slugs'),
    bootstrap: (slug) => api.post(`/sources/bootstrap/${slug}`),
    credentialsSchema: (slug) => api.get(`/sources/bootstrap/${slug}/credentials-schema`),
    paramsSchema: (slug) => api.get(`/sources/bootstrap/${slug}/params-schema`),
};
