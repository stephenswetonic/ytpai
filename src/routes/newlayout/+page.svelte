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
        sessionKey = Date.now();
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

    // Basically a proxy for sendChosenWords()
    function generate() {
        const wordsToCombineJson = JSON.stringify(chosenWordList.items);
        sendChosenWords(wordsToCombineJson);
    }

    async function sendChosenWords(chosenWords) {
        try {
            loadingGenerate = true;
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
        let file = files[0];
        console.log("Uploading file...");
        try {
            await createFile(file, sessionKey);
            loading = true;
            startAudioProcessing();
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // Signal lambda audio analyzer to start processing
    async function startAudioProcessing() {
        try {
            console.log("Starting audio processing...");
            // yptaiBackend lambda function
            const postResponse = await fetch(
                "https://o3dmvj0dij.execute-api.us-east-1.amazonaws.com/audioanalyzer",
                {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                        "Content-Type": "application/json",
                    },
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

            console.log("Audio processing complete.");

            // Add results to the UI
            const result = await postResponse.json();
            generatedWordList.items = result;
            wordDataOriginal = result;
            addTimestamps();
            loading = false;
        } catch (error) {
            console.error("Error during audio processing:", error);
        }
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

<div class="flex flex-col md:flex-row h-screen">
    <!-- Sidebar -->
    <div
        class="sidebar bg-gray-800 text-white w-full md:w-64 md:sticky top-0 h-screen"
    >
        <div class="p-4">
            <h1 class="text-2xl font-bold">Sidebar</h1>

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
        </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6">
        <h1 class="text-3xl font-bold mb-4">Main Content</h1>
        <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam
            scelerisque mauris id velit feugiat, sed suscipit arcu viverra. Duis
            aliquet euismod leo id facilisis. Duis dictum mauris a vestibulum.
        </p>
    </div>
</div>