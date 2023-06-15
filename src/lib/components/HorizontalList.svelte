<svelte:options accessors />
<script>   
    import { flip } from 'svelte/animate';
	import { dndzone } from 'svelte-dnd-action';
    export let items;
    export let containerWidth = '200vw';
    export let itemWidth = '5em';
	let morphDisabled = true;


	const flipDurationMs = 300;
	let dropTargetStyle = {outline: 'rgba(0, 0, 255, 1) solid 2px'};

	function handleDndConsider(e) {
		items = e.detail.items;
	}
	function handleDndFinalize(e) {
		items = e.detail.items;
	}
</script>

<style>
	section {
		margin-left: auto;
		margin-right: auto;
		padding: 0.3em;
		border: 1px solid white;
		overflow-y: auto;
		max-height: 45vh;
		min-height: 5vh;
	}
	div {
		display: inline-block;
		padding: 0.3rem;
		margin: 0.3rem;

	}
</style>
<section class="flex flex-wrap rounded-lg" style="width:{containerWidth}" use:dndzone={{items, flipDurationMs, dropTargetStyle, morphDisabled}} on:consider={handleDndConsider} on:finalize={handleDndFinalize}>
	{#each items as item(item.id)}
		<div class="bg-base-200 rounded text-white" style="{itemWidth}" animate:flip="{{duration: flipDurationMs}}">
			{item.word}	
		</div>
	{/each}
</section>