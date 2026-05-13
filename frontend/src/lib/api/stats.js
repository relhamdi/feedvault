import { api } from './client.js';

export const statsApi = {
    feed: (feedId) => api.get(`/feeds/${feedId}/stats`),
    source: (sourceId) => api.get(`/sources/${sourceId}/stats`),
    collection: (collectionId) => api.get(`/collections/${collectionId}/stats`),
};
