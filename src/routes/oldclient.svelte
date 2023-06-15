<script lang="ts">
    import { onMount } from "svelte";
    import HorizontalList from "$lib/components/HorizontalList.svelte";

    let socket;
    let wordDataOriginal = [];
    let wordData = [];
    let matchedWords = [];
    let wordsToCombine = [];
    let inputText = "";
    let loading;
    let audioElement;

    let generatedWordList;
    let matchedWordList;
    let chosenWordList;

    onMount(() => {
        audioElement = document.getElementById("generatedAudio");
        socket = new WebSocket('ws://localhost:8000');
        socket.binaryType = "arraybuffer";

        socket.onmessage = (event) => {


            if (typeof event.data === "string") {
                console.log(event.data);
                generatedWordList.items = JSON.parse(event.data);
                wordDataOriginal = JSON.parse(event.data);
                loading = false;
            } else if (typeof event.data === "object") {
                const blob = new Blob([event.data], { type: "audio/wav" });
                const url = window.URL.createObjectURL(blob);
                audioElement.src = url;
            }
            
            else {
                console.log(event.data);
            }
        }

        socket.onclose = () => {
            console.log('connection closed');
        }

        socket.onerror = (e) => {
            console.log(e);
        }

        generatedWordList = new HorizontalList({
			target: document.getElementById('generatedWordList'),
			props: {items : wordData, containerWidth: "100%"}
		})

        matchedWordList = new HorizontalList({
			target: document.getElementById('matchedWordList'),
			props: {items : matchedWords, containerWidth: "100%"}
		})

        chosenWordList = new HorizontalList({
			target: document.getElementById('chosenWordList'),
			props: {items : wordsToCombine, containerWidth: "100%"}
		})

    })

    function sendFile() {
        let file = document.getElementById('filename') as HTMLInputElement;
        let reader = new FileReader();
        let rawData = new ArrayBuffer(0);            
        reader.onload = function(e : any) {
            rawData = e.target.result;
            socket.send(rawData);
        }
        reader.readAsArrayBuffer(file.files[0]);
        loading = true;
	}

    function clearCombined() {
        chosenWordList.items = [];
    }

    function addWordsFromInput() {
        generatedWordList.items = wordDataOriginal;
        const wordArray = inputText.split(" ");
        
        let intersection = generatedWordList.items.filter(x => wordArray.includes(x.word));
        matchedWordList.items = intersection;
    }

    function generate() {

        const wordsToCombineJson = JSON.stringify(chosenWordList.items);
        console.log(wordsToCombineJson);
        socket.send(wordsToCombineJson);
    }

</script>

<input type="file" class="file-input w-full max-w-xs" id="filename"/>
<button class="btn btn-primary" on:click={sendFile}>Analyze</button>

{#if loading}
    <span class="loading loading-spinner loading-lg"></span>

{/if}

<h1 class="mt-2 text-3xl font-bold tracking-light text-base-content">Generated Words</h1>
<div id="generatedWordList"></div>

<h1 class="mt-2 text-3xl font-bold tracking-light text-base-content">Type A Sentence</h1>
<input class="input w-full max-w-xl bg-base-200 mt-2"  bind:value={inputText} type="text" placeholder="Type here" />
<button class="btn btn-primary" on:click={addWordsFromInput}>Submit</button>

<h1 class="mt-2 text-3xl font-bold tracking-light text-base-content">Matched Words</h1>
<div id="matchedWordList"></div>


<h1 class="mt-2 text-3xl font-bold tracking-light text-base-content inline-block">Words To Combine</h1>
<button class="btn btn-primary inline-flex" on:click={clearCombined}>clear</button>
<div id="chosenWordList"></div>

<button class="btn btn-primary" on:click={generate}>Generate</button>

<audio controls src="" id="generatedAudio">

</audio>

