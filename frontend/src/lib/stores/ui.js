import { writable } from 'svelte/store';

function persistedStore(key, defaultValue) {
    const stored = localStorage.getItem(key);
    const initial = stored !== null ? JSON.parse(stored) : defaultValue;
    const store = writable(initial);
    store.subscribe((val) => localStorage.setItem(key, JSON.stringify(val)));
    return store;
}

export const openMultiSelectId = writable(null);

export const gridSize = persistedStore('ui:gridSize', 280); // px min card width
