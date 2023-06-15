<script>

	import List from "$lib/components/List.svelte";
	let items1 = [
		{id:"1", title: 'I'},
		{id:"2", title: 'Am'},
		{id:"3", title: 'Yoda'}
	];
	let items2 = [
		{id:"4", title: 'Luke'},
		{id:"5", title: 'Skywalker'}
	];
	
</script>

<hr>
<List items={items1}/>
<hr>
<List items={items2}/>

