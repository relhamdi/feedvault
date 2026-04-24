import { writable } from 'svelte/store';

let nextId = 0;

export const toasts = writable([]);

export function toast(message, type = 'info', duration = 3500) {
    const id = nextId++;
    toasts.update((t) => [...t, { id, message, type, duration }]);
    return id;
}

export function dismissToast(id) {
    toasts.update((t) => t.filter((toast) => toast.id !== id));
}

export const toastSuccess = (msg) => toast(msg, 'success');
export const toastError = (msg) => toast(msg, 'error');
export const toastInfo = (msg) => toast(msg, 'info');
export const toastWarning = (msg) => toast(msg, 'warning', 5000);
