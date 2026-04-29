import { scrapeApi } from '../api/scrape.js';

export const DEFAULT_POLL_INTERVAL = 2000;

export function getPollInterval() {
    return parseInt(localStorage.getItem('pollInterval') ?? DEFAULT_POLL_INTERVAL);
}

export function setPollInterval(val) {
    localStorage.setItem('pollInterval', String(val));
}

export function getDefaultScrapeMode() {
    return localStorage.getItem('defaultScrapeMode') ?? 'INCREMENTAL';
}

export function setDefaultScrapeMode(mode) {
    localStorage.setItem('defaultScrapeMode', mode);
}

/**
 * Poll a scrape job until completion.
 * @param {int} jobId Job ID
 * @param {Object} param1 Object with onDone and onError callbacks
 * @returns Cleanup function to cancel polling
 */
export function pollJob(jobId, { onDone = () => {}, onError = (msg) => {} } = {}) {
    const interval = getPollInterval();
    const id = setInterval(async () => {
        try {
            const job = await scrapeApi.getJob(jobId);
            if (job.status === 'done' || job.status === 'error') {
                clearInterval(id);
                if (job.status === 'error') {
                    onError(job.error_message ?? 'Unknown error');
                } else {
                    onDone(job);
                }
            }
        } catch (e) {
            clearInterval(id);
            console.warn(`Error during pollJob for job ${jobId}:`, e.message);
        }
    }, interval);
    return () => clearInterval(id); // Returns cleanup function
}
