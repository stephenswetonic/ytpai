<script lang="ts">
    import { onMount } from "svelte";
    import List from "$lib/components/List.svelte";
    import { writable } from "svelte/store";
    import Toast from "$lib/components/Toast.svelte";
    import { FFmpeg } from "@ffmpeg/ffmpeg";
    //import RangeSlider from "$lib/components/RangeSlider.svelte";
    //import Video from "$lib/components/Video.svelte";

    const toastMessages = writable([]);

    let ffmpeg;

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
    let hideAudio = true;
    let hideVideo = true;
    let selectedLanguage = "en";

    let generatedWordList;
    let matchedWordList;
    let chosenWordList;

    onMount(() => {
        loadFFmpeg();
        audioElement = document.getElementById("generatedAudio");
        videoElement = document.getElementById("generatedVideo");

        generatedWordList = new List({
            target: document.getElementById("generatedWordList"),
            props: { items: wordData },
        });

        matchedWordList = new List({
            target: document.getElementById("matchedWordList"),
            props: { items: matchedWords },
        });

        chosenWordList = new List({
            target: document.getElementById("chosenWordList"),
            props: { items: wordsToCombine },
        });
    });

    const showToastAlert = (msg) => {
        if (msg.trim() !== "") {
            toastMessages.update((messages) => [...messages, msg]);
        }
    };

    const clearToastMessages = () => {
        toastMessages.set([]); // Clear the toast messages
    };

    function clearCombined() {
        chosenWordList.items = [];
    }

    function addWordsFromInput() {
        generatedWordList.items = wordDataOriginal;
        const wordArray = inputText.split(" ");

        let intersection = generatedWordList.items.filter((x) =>
            wordArray.includes(x.word),
        );
        matchedWordList.items = intersection;
    }

    async function loadFFmpeg() {
        const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm";
        ffmpeg = new FFmpeg();
        await ffmpeg.load({
            coreURL: `${baseURL}/ffmpeg-core.js`,
            wasmURL: `${baseURL}/ffmpeg-core.wasm`,
        });
        console.log("ffmpeg loaded");
    }

    async function readFile(file) {
        return new Promise((resolve) => {
            const fileReader = new FileReader();

            fileReader.onload = () => {
                const { result } = fileReader;
                if (result instanceof ArrayBuffer) {
                    resolve(new Uint8Array(result));
                }
            };
            fileReader.readAsArrayBuffer(file);
        });
    }

    async function trimVideo(video) {
        const videoData = await readFile(video);
        await ffmpeg.writeFile("input.mp4", videoData);
        //await ffmpeg.exec();
    }

    // Basically a proxy for sendChosenWords()
    function generate() {
        const wordsToCombineJson = JSON.stringify(chosenWordList.items);
        sendChosenWords(wordsToCombineJson);
    }

    async function sendChosenWords(chosenWords) {
        try {
            loadingGenerate = true;
            showToastAlert("Generating clip...");
            // yptaiGenerate lambda function
            const response = await fetch(
                "https://o3dmvj0dij.execute-api.us-east-1.amazonaws.com/generate",
                {
                    method: "POST",
                    mode: "cors",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        chosenWords: chosenWords,
                        sessionKey: sessionKey,
                        isVideo: isVideo,
                        audioOnly: audioOnly,
                    }),
                },
            );

            // Turn response into a blob and add to page
            let buffer = await response.arrayBuffer();
            let blob;
            let url;
            if (!audioOnly) {
                blob = new Blob([buffer], { type: "video/mp4" });
                url = window.URL.createObjectURL(blob);
                videoElement.src = url;
                hideVideo = false;
            } else {
                blob = new Blob([buffer], { type: "audio/wav" });
                url = window.URL.createObjectURL(blob);
                audioElement.src = url;
                hideAudio = false;
            }
            loadingGenerate = false;
            clearToastMessages();
        } catch (error) {
            console.log(error);
        }
    }

    // Get signed url for uploading to S3
    async function getSignedUrl(key) {
        try {
            const API_ENDPOINT =
                "https://o3dmvj0dij.execute-api.us-east-1.amazonaws.com/uploads?key=" +
                key;
            const response = await fetch(API_ENDPOINT, {
                method: "GET",
            });
            const result = await response.json();
            return result;
        } catch (error) {
            console.error("Error getting signed url: ", error);
        }
    }

    // Send file to upload to S3
    async function createFile(file, key) {
        // Wrapped in a promise so this can be awaited
        return new Promise<void>(async (resolve, reject) => {
            try {
                // Get signed url
                const signedUrlResult = await getSignedUrl(key);

                let reader = new FileReader();
                reader.readAsArrayBuffer(file); // This triggers reader.onload

                reader.onload = async (e) => {
                    try {
                        const response = await fetch(
                            signedUrlResult.uploadURL,
                            {
                                method: "PUT",
                                body: e.target.result,
                            },
                        );

                        if (!response.ok) {
                            throw new Error("Failed to upload file");
                        }

                        console.log("File uploaded successfully.");
                        showToastAlert("File uploaded successfully.");
                        resolve(); // Resolve the promise when the upload is successful
                    } catch (error) {
                        console.error("Error uploading file: ", error);
                        reject(error); // Reject the promise if there's an error during upload
                    }
                };
            } catch (error) {
                console.error("Error getting signed URL: ", error);
                reject(error); // Reject the promise if there's an error getting the signed URL
            }
        });
    }

    // Uploads file to S3 and starts processing audio
    async function upload() {
        // Create new session key to match this upload to the file in s3
        sessionKey = Date.now();

        let file = files[0];
        console.log("Uploading file...");
        showToastAlert("Uploading file...");
        try {
            loading = true;
            await createFile(file, sessionKey);
            startAudioProcessing();
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // Signal lambda audio analyzer to start processing
    async function startAudioProcessing() {
        try {
            console.log("Starting audio processing...");
            showToastAlert("Processing audio...");
            // yptaiBackend lambda function
            const postResponse = await fetch(
                "https://o3dmvj0dij.execute-api.us-east-1.amazonaws.com/audioanalyzer",
                {
                    method: "POST",
                    body: JSON.stringify({
                        sessionKey: sessionKey,
                        isVideo: isVideo,
                        audioOnly: audioOnly,
                        useBigModel: useBigModel,
                        lang: selectedLanguage,
                    }),
                },
            );

            if (!postResponse.ok) {
                throw new Error(`HTTP error! Status: ${postResponse.status}`);
            }

            // Ping S3 until the results are retrieved or timeout
            // Set at 5 min timeout
            const result = await pingWordsJson(sessionKey, 60, 5000);
            const resultJson = await result.json();

            // Add words to the UI
            generatedWordList.items = resultJson;
            wordDataOriginal = resultJson;
            addTimestamps();
            loading = false;
            clearToastMessages();
        } catch (error) {
            console.error("Error during audio processing:", error);
        }
    }

    // Try to get processed words from s3
    // delay in ms
    async function pingWordsJson(sessionKey, maxAttempts, delay) {
        let attempts = 0;

        async function ping() {
            attempts++;

            const response = await fetch(
                "https://sam-app-s3uploadbucket-qkgqfgtltuzq.s3.amazonaws.com/" +
                    sessionKey +
                    ".json",
            );
            if (response.ok) {
                return response; // File successfully received
            } else if (attempts < maxAttempts) {
                await new Promise((resolve) => setTimeout(resolve, delay)); // Retry after delay
                return await ping();
            } else {
                return null;
            }
        }
        return await ping(); // Start the initial ping
    }

    // Adds placeholders in the word list to give reference to time
    // The 'end' value is set to 'xyz' to discriminate them
    function addTimestamps() {
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
                    minutes += 1;
                }
                generatedWordList.items.splice(i, 0, {
                    id: String(threshold),
                    end: "xyz",
                    word: minutes + ":" + String(seconds).padStart(2, "0"),
                });
                generatedWordList.items = generatedWordList.items;
                threshold += step;
            }
        }
    }

    // Check if input is video/audio and set accordingly
    function checkInput() {
        if (files[0].type == "video/mp4") {
            audioOnly = false;
            isVideo = true;
        } else {
            // If file is audio, disable the switch
            audioOnly = true;
            audioOnlyDisabled = true;
        }
    }
</script>

<div role="alert" class="alert">
    <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        class="stroke-info shrink-0 w-6 h-6"
        ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        ></path></svg
    >
    <span
        >The more accurate "Big Model" for English is now working! Files that
        take longer than 5 minutes to process will time out for now.</span
    >
</div>

<Toast bind:messages={$toastMessages} duration={3000} />

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
    <input
        type="checkbox"
        class="toggle toggle-lg inline-flex"
        bind:checked={audioOnly}
        disabled={audioOnlyDisabled}
    />

    <div
        class="my-auto ml-1 mr-3 tooltip"
        data-tip="Generate final clip as audio only"
    >
        <svg
            class="my-auto mx-1"
            width="20px"
            height="20px"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            stroke="#ffffff"
        >
            <g id="SVGRepo_bgCarrier" stroke-width="0" />
            <g
                id="SVGRepo_tracerCarrier"
                stroke-linecap="round"
                stroke-linejoin="round"
            />
            <g id="SVGRepo_iconCarrier">
                <g clip-path="url(#clip0_429_11043)">
                    <circle
                        cx="12"
                        cy="11.9999"
                        r="9"
                        stroke="#ffffff"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                    <rect
                        x="12"
                        y="16"
                        width="0.01"
                        height="0.01"
                        stroke="#ffffff"
                        stroke-width="3.75"
                        stroke-linejoin="round"
                    />
                    <path
                        d="M10.5858 7.58572C10.9754 7.1961 11.4858 7.00083 11.9965 6.99994C12.5095 6.99904 13.0228 7.1943 13.4142 7.58572C13.8047 7.97625 14 8.48809 14 8.99994C14 9.51178 13.8047 10.0236 13.4142 10.4141C13.0228 10.8056 12.5095 11.0008 11.9965 10.9999L12 11.9999"
                        stroke="#ffffff"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                </g>
                <defs>
                    <clipPath id="clip0_429_11043">
                        <rect width="24" height="24" fill="white" />
                    </clipPath>
                </defs>
            </g>
        </svg>
    </div>
</div>

<div class="inline-flex">
    <div class="my-auto mx-1">Big Model</div>
    <input
        type="checkbox"
        class="toggle toggle-lg inline-flex"
        bind:checked={useBigModel}
    />

    <div
        class="my-auto mx-1 tooltip"
        data-tip="More accurate speech recognition model at the cost of speed (English only)"
    >
        <svg
            class="my-auto mx-1"
            width="20px"
            height="20px"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            stroke="#ffffff"
        >
            <g id="SVGRepo_bgCarrier" stroke-width="0" />
            <g
                id="SVGRepo_tracerCarrier"
                stroke-linecap="round"
                stroke-linejoin="round"
            />
            <g id="SVGRepo_iconCarrier">
                <g clip-path="url(#clip0_429_11043)">
                    <circle
                        cx="12"
                        cy="11.9999"
                        r="9"
                        stroke="#ffffff"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                    <rect
                        x="12"
                        y="16"
                        width="0.01"
                        height="0.01"
                        stroke="#ffffff"
                        stroke-width="3.75"
                        stroke-linejoin="round"
                    />
                    <path
                        d="M10.5858 7.58572C10.9754 7.1961 11.4858 7.00083 11.9965 6.99994C12.5095 6.99904 13.0228 7.1943 13.4142 7.58572C13.8047 7.97625 14 8.48809 14 8.99994C14 9.51178 13.8047 10.0236 13.4142 10.4141C13.0228 10.8056 12.5095 11.0008 11.9965 10.9999L12 11.9999"
                        stroke="#ffffff"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                </g>
                <defs>
                    <clipPath id="clip0_429_11043">
                        <rect width="24" height="24" fill="white" />
                    </clipPath>
                </defs>
            </g>
        </svg>
    </div>
</div>

<select
    bind:value={selectedLanguage}
    class="select select-primary w-full max-w-xs"
>
    <option selected value="en">English</option>
    <option value="es">Spanish</option>
    <option value="fr">French</option>
    <option value="ru">Russian</option>
    <option value="de">German</option>
</select>
<button class="btn btn-primary" on:click|preventDefault={upload}>Analyze</button
>

{#if loading}
    <div class="inline-flex h-full align-middle">
        <span class="loading loading-spinner loading-lg"></span>
    </div>
{/if}
<div class="text-sm">Supports audio (.wav) or video (.mp4)</div>

<ul class="text-sm">
    <li>
        To multi drag with the mouse use <code>ctrl + click</code> or
        <code>cmd + click</code> to add items before dragging.
    </li>
    <li>
        To multi drag with keyboard, tab to items and use <code
            >ctrl + shift</code
        >
        or <code>cmd + shift</code> to add items before entering "drag mode" by
        hitting <code>space</code>
    </li>
</ul>

<h1 class="mt-2 text-xl font-bold tracking-light text-base-content">
    Generated Words
</h1>
<div id="generatedWordList"></div>

<h1 class="mt-2 text-xl font-bold tracking-light text-base-content">
    Filter Words
</h1>
<input
    class="input w-full max-w-xl bg-base-200 mt-2"
    bind:value={inputText}
    type="text"
    placeholder="Type here"
/>
<button class="btn btn-primary" on:click={addWordsFromInput}>Submit</button>

<h1 class="mt-2 text-xl font-bold tracking-light text-base-content">
    Matched Words
</h1>
<div id="matchedWordList"></div>

<h1
    class="mt-2 text-xl font-bold tracking-light text-base-content inline-block"
>
    Words To Combine
</h1>
<button class="btn btn-sm btn-primary inline-flex m-1" on:click={clearCombined}
    >clear</button
>
<div id="chosenWordList"></div>

<button class="btn btn-primary btn-wide mt-4" on:click={generate}
    >Generate</button
>
{#if loadingGenerate}
    <div class="inline-flex h-full align-middle">
        <span class="loading loading-spinner loading-lg"></span>
    </div>
{/if}

<audio class="my-2" controls src="" id="generatedAudio" hidden={hideAudio}>
</audio>
{#if !hideAudio}
    <a
        href={audioElement?.src}
        download
        class="btn btn-primary inline-flex mb-4">Download</a
    >
{/if}

<!-- svelte-ignore a11y-media-has-caption -->
<video class="my-2" src="" id="generatedVideo" controls hidden={hideVideo}
></video>
{#if !hideVideo}
    <a
        href={videoElement?.src}
        download
        class="btn btn-primary inline-flex mb-4">Download</a
    >
{/if}
