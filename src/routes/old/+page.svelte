<script lang="ts">
    import { onMount } from "svelte";
    import List from "$lib/components/List.svelte";
    import { PUBLIC_BACKEND_URL } from '$env/static/public';

    let files;
    let sessionKey;
    let wordDataOriginal = [];
    let wordData = [];
    let matchedWords = [];
    let wordsToCombine = [];
    let inputText = "";
    let loading = false;
    let loadingGenerate = false;
    let audioOnly = true;
    let isVideo = false;
    let audioOnlyDisabled = false;
    let useBigModel = false;
    let audioElement;
    let videoElement;
    let hideAudio = true
    let hideVideo = true
    let selectedLanguage = "en";

    let generatedWordList;
    let matchedWordList;
    let chosenWordList;


    onMount(() => {
        sessionKey = Date.now();
        audioElement = document.getElementById("generatedAudio");
        videoElement = document.getElementById("generatedVideo");

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

    // Clears UI list of chosen words
    function clearChosenWords() {
        chosenWordList.items = [];
    }

    // Adds words to the UI based on a sentence
    function addWordsFromInput() {
        generatedWordList.items = wordDataOriginal;
        const wordArray = inputText.split(" ");
        
        let intersection = generatedWordList.items.filter(x => wordArray.includes(x.word));
        matchedWordList.items = intersection;
    }

    // Converts chosen words in the UI to JSON and sends to backend
    function generate() {
        const wordsToCombineJson = JSON.stringify(chosenWordList.items);
        sendChosenWords(wordsToCombineJson);
    }

    // Sends the chosen words to the backend. Receives an audio or video file in response.
    async function sendChosenWords(chosenWords) {
        try {
            loadingGenerate = true;
            const response = await fetch(PUBLIC_BACKEND_URL + "/generate", {
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

    // Uploads the audio/video to the backend. Receives the parsed words and timestamps in response.
    async function upload(formData) {
        try {
            loading = true;
            const response = await fetch(PUBLIC_BACKEND_URL + "/source", {
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

    // Adds timestamp placeholders to the UI
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

    // Send audio/video etc as form data to the backend
    function sendSource() {
        try {
            const formData = new FormData();
            formData.append("key", sessionKey);
            formData.append("isVideo", String(isVideo));
            formData.append("useBigModel", String(useBigModel));
            formData.append("file", files[0]);
            formData.append("lang", selectedLanguage);
            upload(formData);
        } catch(err) {
            console.log(err);
        }
        
    }

    // Check is selected file is audio or video
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
    class="file-input w-full max-w-sm mt-2"
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

    <div class="my-auto ml-1 mr-3 tooltip" data-tip="Generate final clip as audio only">
        <svg class="my-auto mx-1" width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="#ffffff">
            <g id="SVGRepo_bgCarrier" stroke-width="0"/>
            <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"/>
            <g id="SVGRepo_iconCarrier"> <g clip-path="url(#clip0_429_11043)"> <circle cx="12" cy="11.9999" r="9" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/> <rect x="12" y="16" width="0.01" height="0.01" stroke="#ffffff" stroke-width="3.75" stroke-linejoin="round"/> <path d="M10.5858 7.58572C10.9754 7.1961 11.4858 7.00083 11.9965 6.99994C12.5095 6.99904 13.0228 7.1943 13.4142 7.58572C13.8047 7.97625 14 8.48809 14 8.99994C14 9.51178 13.8047 10.0236 13.4142 10.4141C13.0228 10.8056 12.5095 11.0008 11.9965 10.9999L12 11.9999" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/> </g> <defs> <clipPath id="clip0_429_11043"> <rect width="24" height="24" fill="white"/> </clipPath> </defs> </g>
        </svg>
    </div>
</div>
<div class="inline-flex">
    <div class="my-auto mx-1">Big Model</div>
    <input type="checkbox" class="toggle toggle-lg inline-flex" bind:checked={useBigModel}/>

    <div class="my-auto mx-1 tooltip" data-tip="More accurate speech recognition model at the cost of speed (English only)">
        <svg class="my-auto mx-1" width="20px" height="20px" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="#ffffff">
            <g id="SVGRepo_bgCarrier" stroke-width="0"/>
            <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"/>
            <g id="SVGRepo_iconCarrier"> <g clip-path="url(#clip0_429_11043)"> <circle cx="12" cy="11.9999" r="9" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/> <rect x="12" y="16" width="0.01" height="0.01" stroke="#ffffff" stroke-width="3.75" stroke-linejoin="round"/> <path d="M10.5858 7.58572C10.9754 7.1961 11.4858 7.00083 11.9965 6.99994C12.5095 6.99904 13.0228 7.1943 13.4142 7.58572C13.8047 7.97625 14 8.48809 14 8.99994C14 9.51178 13.8047 10.0236 13.4142 10.4141C13.0228 10.8056 12.5095 11.0008 11.9965 10.9999L12 11.9999" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/> </g> <defs> <clipPath id="clip0_429_11043"> <rect width="24" height="24" fill="white"/> </clipPath> </defs> </g>
        </svg>
    </div>
</div>
<select bind:value={selectedLanguage} class="select select-primary w-full max-w-xs">
    <option selected value="en">English</option>
    <option value="es">Spanish</option>
    <option value="fr">French</option>
    <option value="ru">Russian</option>
    <option value="de">German</option>
</select>
<button class="btn btn-primary" on:click|preventDefault={sendSource}>Analyze</button>


{#if loading}
<div class="inline-flex h-full align-middle">
    <span class="loading loading-spinner loading-lg"></span>
</div>
{/if}
<div class="text-sm">Supports audio (.wav) or video (.mp4) under 100MB</div>
<div class="text-sm">Long videos may time out!</div>

<ul class="text-sm">
	<li>To multi drag with the mouse use <code>ctrl + click</code> or <code>cmd + click</code> to add items before dragging.</li>
	<li>To multi drag with keyboard, tab to items and use <code>ctrl + shift</code> or <code>cmd + shift</code> to add items before entering "drag mode" by hitting <code>space</code></li>
</ul>

<h1 class="mt-2 text-xl font-bold tracking-light text-base-content">Generated Words</h1>
<div id="generatedWordList"></div>

<h1 class="mt-2 text-xl font-bold tracking-light text-base-content">Filter Words</h1>
<input class="input w-full max-w-xl bg-base-200 mt-2"  bind:value={inputText} type="text" placeholder="Type here" />
<button class="btn btn-primary" on:click={addWordsFromInput}>Submit</button>

<h1 class="mt-2 text-xl font-bold tracking-light text-base-content">Matched Words</h1>
<div id="matchedWordList"></div>


<h1 class="mt-2 text-xl font-bold tracking-light text-base-content inline-block">Words To Combine</h1>
<button class="btn btn-sm btn-primary inline-flex m-1" on:click={clearChosenWords}>clear</button>
<div id="chosenWordList"></div>

<button class="btn btn-primary btn-wide mt-4" on:click={generate}>Generate</button>
{#if loadingGenerate}
<div class="inline-flex h-full align-middle">
    <span class="loading loading-spinner loading-lg"></span>
</div>
{/if}


<audio class="my-2" controls src="" id="generatedAudio" hidden={hideAudio}>
    
</audio>
{#if !hideAudio}
    <a href={audioElement?.src} download class="btn btn-primary inline-flex mb-4">Download</a>
{/if}


<!-- svelte-ignore a11y-media-has-caption -->
<video class="my-2" src="" id="generatedVideo" controls hidden={hideVideo}></video>
{#if !hideVideo}
    <a href={videoElement?.src} download class="btn btn-primary inline-flex mb-4">Download</a>
{/if}



