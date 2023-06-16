<svelte:options accessors />
<script>
	import {dndzone, TRIGGERS, SOURCES, DRAGGED_ELEMENT_ID} from 'svelte-dnd-action';
	import {flip} from 'svelte/animate';
	import {tick} from "svelte";
	import {activeZoneId, selectedItems} from "./selectionStore";
	const flipDurationMs = 120;
	
	export let items = [];
	let zoneId = `zone-${Math.floor(Math.random() * 1000000)}`;
	let dropTargetStyle = {outline: 'rgba(0, 0, 255, 1) solid 2px'};
	let morphDisabled = true;
	let autoAriaDisabled = true;
	
	function transformDraggedElement(el) {
		if (!el.getAttribute("data-selected-items-count") && Object.keys($selectedItems).length) {
			el.setAttribute("data-selected-items-count", Object.keys($selectedItems).length + 1);
		}
  }
	function handleConsider(e) {
		const {items: newItems, info: {trigger, source, id}} = e.detail;
		if (source !== SOURCES.KEYBOARD) {
			if (Object.keys($selectedItems).length && trigger === TRIGGERS.DRAG_STARTED) {
				if (Object.keys($selectedItems).includes(id)) {
					delete($selectedItems[id]);
					$selectedItems = {...$selectedItems};
					tick().then(() => {
						items = newItems.filter(item => !Object.keys($selectedItems).includes(item.id));
					});
				} else {
					$selectedItems = {};
				}
			}
		}
		if (trigger === TRIGGERS.DRAG_STOPPED) $selectedItems = {};
		items = newItems;
	}
	function handleFinalize(e) {
		let {items: newItems, info: {trigger, source, id}} = e.detail;	
		if (Object.keys($selectedItems).length) {
			if (trigger === TRIGGERS.DROPPED_INTO_ANOTHER) {
				items = newItems.filter(item => !Object.keys($selectedItems).includes(item.id));
			} else if (trigger === TRIGGERS.DROPPED_INTO_ZONE || trigger === TRIGGERS.DROPPED_OUTSIDE_OF_ANY) {
				tick().then(() => {
					const idx = newItems.findIndex(item => item.id === id);
					// to support arrow up when keyboard dragging
					const sidx = Math.max(Object.values($selectedItems).findIndex(item => item.id === id), 0);
					newItems = newItems.filter(item => !Object.keys($selectedItems).includes(item.id)) 
					newItems.splice(idx - sidx, 0, ...Object.values($selectedItems));
					items = newItems;
					$activeZoneId = zoneId;
					if (source !== SOURCES.KEYBOARD) $selectedItems = {}; 
				});
			}
		} else {
			items = newItems;	
		}
	}
	function handleMaybeSelect(id, e) {
		if (!e.ctrlKey && !e.metaKey) return;
		if (e.key && e.key !== "Shift") return;
		if ($activeZoneId !== zoneId) {
			$selectedItems = {};
			$activeZoneId = zoneId;
		}
		if (Object.keys($selectedItems).includes(id)) {
			delete($selectedItems[id]);
		} else {
			$selectedItems[id] = items.find(item => item.id === id);
		}
		$selectedItems = {...$selectedItems};
	}
</script>

<section class="rounded-lg" use:dndzone={{items, flipDurationMs, morphDisabled, dropTargetStyle, autoAriaDisabled, transformDraggedElement}} on:consider={handleConsider} on:finalize={handleFinalize}>
	{#each items as item(item.id)}
		<div class="rounded align-middle" animate:flip={{duration:flipDurationMs}} class:selected={Object.keys($selectedItems).includes(item.id)} on:mousedown={(e) => handleMaybeSelect(item.id, e)} on:keydown={(e) => handleMaybeSelect(item.id, e)}>
			{item.word}	
		</div>
	{/each}
</section>

<style>
	div {
		display: inline-block;
		padding: 0.3rem;
		margin: 0.3rem;
	}
	section {
        display: flex;
        flex-wrap: wrap;
		margin-left: auto;
		margin-right: auto;
		padding: 0.3em;
		border: 1px solid white;
		overflow-y: auto;
		max-height: 45vh;
		min-height: 5vh;
	}
	.selected {
		background-color: darkslategrey;
	}
	:global([data-selected-items-count]::after) {
		position: absolute;
		right: 0.2em;
		padding: 0.1em;
		content: attr(data-selected-items-count);
		color: white;
		background: rgba(0, 0, 0, 0.6);
	}
</style>
