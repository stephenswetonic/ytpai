import {writable} from "svelte/store";
export const activeZoneId = writable();

// id -> item
export const selectedItems = writable({});