import { api } from './client.js';

export const scrapeApi = {
    scrape: (data) => api.post('/scrape/', data),
    getJob: (jobId) => api.get(`/scrape/jobs/${jobId}`),
    listJobs: (params = {}) => {
        const query = new URLSearchParams(params);
        return api.get(`/scrape/jobs?${query}`);
    },
    deleteJob: (jobId) => api.delete(`/scrape/jobs/${jobId}`),
    getLogs: (jobId) => api.get(`/scrape/jobs/${jobId}/logs`),
};
