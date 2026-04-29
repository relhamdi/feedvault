import { API_BASE_URL, API_URL } from '../config.js';

/**
 * Base fetch wrapper. Throws on non-2xx responses.
 */
async function rawFetch(path, options = {}, jsonBody = false) {
    const headers = jsonBody ? { 'Content-Type': 'application/json' } : {};
    const response = await fetch(`${API_URL}${path}`, { headers, ...options });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response;
}

async function request(path, options = {}) {
    const response = await rawFetch(path, options, true);
    return response.status === 204 ? null : response.json();
}

export const rootApi = {
    health: () => fetch(`${API_BASE_URL}/health`).then((r) => r.json()),
    stats: () => fetch(`${API_BASE_URL}/stats`).then((r) => r.json()),
};

export const api = {
    get: (path) => request(path),
    post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
    patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
    put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
    delete: (path) => request(path, { method: 'DELETE' }),
    upload: (path, formData) =>
        rawFetch(path, { method: 'POST', body: formData }).then((r) =>
            r.status === 204 ? null : r.json()
        ),
    download: (path, body) => rawFetch(path, { method: 'POST', body: JSON.stringify(body) }, true),
};
