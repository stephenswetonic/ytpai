<script lang="ts">
    import { onMount } from "svelte";
    import List from "$lib/components/List.svelte";

    let files;
    let sessionKey;
    let wordDataOriginal = [];
    let wordData = [];
    let matchedWords = [];
    let wordsToCombine = [];
    let inputText = "";
    let loading;
    let loadingGenerate;
    let audioOnly = true;
    let isVideo = false;
    let audioOnlyDisabled = false;
    let audioElement;
    let videoElement;
    let hideAudio = true
    let hideVideo = true

    let generatedWordList;
    let matchedWordList;
    let chosenWordList;

    let testItems;

    onMount(() => {
        sessionKey = Date.now();
        audioElement = document.getElementById("generatedAudio");
        videoElement = document.getElementById("generatedVideo");

        testItems = [
        {id : 0, end : 1, word : "word"},
        {id : 1, end : 2, word : "word2"},
        {id : 2, end : 3, word : "word3"}
    ]

        generatedWordList = new List({
			target: document.getElementById('generatedWordList'),
			props: {items : wordData}
		})

        matchedWordList = new List({
			target: document.getElementById('matchedWordList'),
			props: {items : matchedWords }
		})

        chosenWordList = new List({
			target: document.getElementById('chosenWordList'),
			props: {items : wordsToCombine}
		})

    })

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
        sendChosenWords(wordsToCombineJson);
    }

    async function sendChosenWords(chosenWords) {
        try {
            loadingGenerate = true;
            const response = await fetch("http://localhost:8000/generate", {
                method: "PUT",
                mode: "cors",
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify( {"chosenWords": chosenWords, "sessionKey" : sessionKey, "isVideo" : isVideo, "audioOnly" : audioOnly})
            });
            
            let buffer = await response.arrayBuffer();
            let blob;
            let url;
            if (!audioOnly) {
                blob = new Blob([buffer], { type: "video/mp4" });
                url = window.URL.createObjectURL(blob);
                videoElement.src = url;
                hideVideo = false
            } else {
                blob = new Blob([buffer], { type: "audio/wav" });
                url = window.URL.createObjectURL(blob);
                audioElement.src = url;
                hideAudio = false
            }
            loadingGenerate = false;
        } catch (error) {
            console.log(error);
        }
    }

    async function upload(formData) {
        try {
            loading = true;
            const response = await fetch("http://localhost:8000/source", {
            method: "PUT",
            mode: "cors",
            body: formData
            });
            
            const result = await response.json();
            generatedWordList.items = JSON.parse(result.wordsJson);
            wordDataOriginal = JSON.parse(result.wordsJson);
            await addTimestamps();
            loading = false;
        } catch (error) {
            console.error("Error:", error);
        }
    }

    async function addTimestamps() {
        let seconds = 0;
        let minutes = 0;
        let pointer;
        let step = 10; 
        let threshold = step;
        
        for (let i = 0; i < generatedWordList.items.length; i++) {
            pointer = generatedWordList.items[i];
            if (Number(pointer["id"]) > threshold) {
                seconds += step;
                if (seconds == 60) {
                    seconds = 0;
                    minutes += 1
                }
                generatedWordList.items.splice(i, 0, {"id" : String(threshold), "end" : "xyz", "word" : (minutes + ":" + String(seconds).padStart(2, "0"))});
                generatedWordList.items = generatedWordList.items;
                threshold += step;                
            }
        }
    }

    function sendSource() {
        const formData = new FormData();
        formData.append("key", sessionKey);
        formData.append("isVideo", String(isVideo))
        formData.append("file", files[0]);
        upload(formData);
    }

    function checkInput() {
        if (files[0].type == "video/mp4") {
            audioOnly = false;
            isVideo = true;
        } else {
            audioOnly = true;
            audioOnlyDisabled = true;
        }
    }
</script>



<input 
    class="file-input w-full max-w-sm mt-6"
    accept="audio/wav, video/mp4"
    bind:files
    id="source"
    name="source"
    type="file"
    on:change={checkInput}
/>

<div class="inline-flex">
    <div class="my-auto mx-1">Audio Only</div>
    <input type="checkbox" class="toggle toggle-lg inline-flex" bind:checked={audioOnly} disabled={audioOnlyDisabled} />
</div>
<button class="btn btn-primary" on:click|preventDefault={sendSource}>Analyze</button>

{#if loading}
<div class="inline-flex h-full align-middle">
    <span class="loading loading-spinner loading-lg"></span>
</div>
{/if}
<div>Supports audio (.wav) or video (.mp4)</div>

<ul>
	<li>To multi drag with the mouse use <code>ctrl + click</code> or <code>cmd + click</code> to add items before dragging.</li>
	<li>To multi drag with keyboard, tab to items and use <code>ctrl + shift</code> or <code>cmd + shift</code> to add items before entering "drag mode" by hitting <code>space</code></li>
</ul>

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
{#if loadingGenerate}
    <span class="loading loading-spinner loading-lg my-auto"></span>
{/if}


<audio controls src="" id="generatedAudio" hidden={hideAudio}>
    
</audio>
{#if !hideAudio}
    <a href={audioElement?.src} download >Download</a>
{/if}


<!-- svelte-ignore a11y-media-has-caption -->
<video src="" id="generatedVideo" controls hidden={hideVideo}></video>



