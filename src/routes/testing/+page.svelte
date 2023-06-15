<script>


    import List from "$lib/components/List.svelte";




    let testItems = [
        {id : "0", end : 1, word : "word"},
        {id : "1", end : 2, word : "word2"},
        {id : "2", end : 3, word : "word3"}
        ];
    let testItems2 = [
        {id : "3", end : 1, word : "word4"},
        {id : "4", end : 2, word : "word5"},

        ];



 


  



</script>

<List items={testItems}/>
<List items={testItems2}/>





