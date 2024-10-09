<script lang="ts">
    import { onMount } from "svelte";
    import { writable } from "svelte/store";
    import Toast from "$lib/components/Toast.svelte";
    import FileDropZone from "$lib/components/FileDropZone.svelte";
    import DraggableZones from "$lib/components/DraggableZones.svelte";
    import { _serverStatus } from '../stores/serverStatus';

    const toastMessages = writable([]);
    let sourceFile;
    let trimmedFile;
    let startTime;
    let endTime;
    let sessionKey;
    let wordDataOriginal = [];
    let loading = false;
    let loadingGenerate = false;
    let audioOnly = true;
    let isVideo = false;
    let audioOnlyDisabled = false;
    let audioElement;
    let videoElement;
    let hideAudio = true;
    let hideVideo = true;
    let replaceWordsToMix = false;
    let selectedLanguage = "auto";

    let generatedWords = [];
    let chosenWords;
    let draggableZonesComponent;

    // Runs when sourceFile changes
    $: if (sourceFile) {
        checkInput();
    }

    onMount(() => {
        audioElement = document.getElementById("generatedAudio");
        videoElement = document.getElementById("generatedVideo");
    });


    const showToastAlert = (msg) => {
        if (msg.trim() !== "") {
            toastMessages.update((messages) => [...messages, msg]);
        }
    };

    const clearToastMessages = () => {
        toastMessages.set([]); // Clear the toast messages
    };

    // Basically a proxy for sendChosenWords()
    function generate() {
        const wordsToCombineJson = JSON.stringify(chosenWords);
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

            //TODO Check actual file types
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

        showToastAlert("Uploading file...");
        try {
            loading = true;
            await createFile(trimmedFile, sessionKey);
            startAudioProcessing();
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // Signal lambda audio analyzer to start processing
    async function startAudioProcessing() {
        let startTime = Date.now();
        try {
            showToastAlert("Processing audio...");            
            const postResponse = await fetch(
                "https://stag-thankful-buck.ngrok-free.app/analyze",

                {
                    method: "POST",
                    mode: "cors",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        sessionKey: String(sessionKey),
                        isVideo: isVideo,
                        audioOnly: audioOnly,
                        lang: selectedLanguage,
                    }),
                },
            );

            if (!postResponse.ok) {
                throw new Error(`HTTP error! Status: ${postResponse.status}`);
            }

            let resultJson = await postResponse.json();
            let newWords = resultJson.body;

            generatedWords = newWords;

            // Add words to the UI
            // if (replaceWordsToMix) {
            //     generatedWords = newWords;
            // } else {
            //     // Create a tab..
            //     generatedWords = generatedWords.concat(newWords);
            // }
            
            draggableZonesComponent.fillWords(generatedWords);

            wordDataOriginal = resultJson;
            //addTimestamps();
            loading = false;
            clearToastMessages();

            let timeTaken = Date.now() - startTime;
            console.log(formatTime(timeTaken));
        } catch (error) {
            console.error("Error during audio processing:", error);
        }
    }

    // Convert milliseconds to seconds
    function formatTime(milliseconds) {
        let totalSeconds = Math.floor(milliseconds / 1000);

        // Calculate minutes and remaining seconds
        let minutes = Math.floor(totalSeconds / 60);
        let seconds = totalSeconds % 60;

        // Return formatted string
        return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
    }

    // Check if input is video/audio and set accordingly
    function checkInput() {
        if (
            sourceFile.type == "video/mp4" ||
            sourceFile.type == "video/webm" ||
            sourceFile.type == "video/quicktime"
        ) {
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
        >Now using WhisperX on an RTX 3080 for faster processing and more accurate results.
         The server is in the US west coast, so distance will vary your processing time.</span
    >
</div>

{#if $_serverStatus === 'down'}
<div role="alert" class="alert alert-error">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-6 w-6 shrink-0 stroke-current"
      fill="none"
      viewBox="0 0 24 24">
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>The server is currently down. Please try again later.</span>
  </div>
{/if}

<Toast bind:messages={$toastMessages} duration={3000} />

<FileDropZone bind:sourceFile bind:trimmedFile bind:startTime bind:endTime />


<select
    bind:value={selectedLanguage}
    class="select select-primary w-full max-w-xs"
>
    <option selected value="auto">Auto Detect</option>
    <option value="en">English</option>
    <option value="zh">Chinese</option>
    <option value="de">German</option>
    <option value="es">Spanish</option>
    <option value="ru">Russian</option>
    <option value="ko">Korean</option>
    <option value="fr">French</option>
    <option value="ja">Japanese</option>
    <option value="pt">Portuguese</option>
    <option value="tr">Turkish</option>
    <option value="pl">Polish</option>
    <option value="ca">Catalan</option>
    <option value="nl">Dutch</option>
    <option value="ar">Arabic</option>
    <option value="sv">Swedish</option>
    <option value="it">Italian</option>
    <option value="id">Indonesian</option>
    <option value="hi">Hindi</option>
    <option value="fi">Finnish</option>
    <option value="vi">Vietnamese</option>
    <option value="he">Hebrew</option>
    <option value="uk">Ukrainian</option>
    <option value="el">Greek</option>
    <option value="ms">Malay</option>
    <option value="cs">Czech</option>
    <option value="ro">Romanian</option>
    <option value="da">Danish</option>
    <option value="hu">Hungarian</option>
    <option value="ta">Tamil</option>
    <option value="no">Norwegian</option>
    <option value="th">Thai</option>
    <option value="ur">Urdu</option>
    <option value="hr">Croatian</option>
    <option value="bg">Bulgarian</option>
    <option value="lt">Lithuanian</option>
    <option value="la">Latin</option>
    <option value="mi">Maori</option>
    <option value="ml">Malayalam</option>
    <option value="cy">Welsh</option>
    <option value="sk">Slovak</option>
    <option value="te">Telugu</option>
    <option value="fa">Persian</option>
    <option value="lv">Latvian</option>
    <option value="bn">Bengali</option>
    <option value="sr">Serbian</option>
    <option value="az">Azerbaijani</option>
    <option value="sl">Slovenian</option>
    <option value="kn">Kannada</option>
    <option value="et">Estonian</option>
    <option value="mk">Macedonian</option>
    <option value="br">Breton</option>
    <option value="eu">Basque</option>
    <option value="is">Icelandic</option>
    <option value="hy">Armenian</option>
    <option value="ne">Nepali</option>
    <option value="mn">Mongolian</option>
    <option value="bs">Bosnian</option>
    <option value="kk">Kazakh</option>
    <option value="sq">Albanian</option>
    <option value="sw">Swahili</option>
    <option value="gl">Galician</option>
    <option value="mr">Marathi</option>
    <option value="pa">Punjabi</option>
    <option value="si">Sinhala</option>
    <option value="km">Khmer</option>
    <option value="sn">Shona</option>
    <option value="yo">Yoruba</option>
    <option value="so">Somali</option>
    <option value="af">Afrikaans</option>
    <option value="oc">Occitan</option>
    <option value="ka">Georgian</option>
    <option value="be">Belarusian</option>
    <option value="tg">Tajik</option>
    <option value="sd">Sindhi</option>
    <option value="gu">Gujarati</option>
    <option value="am">Amharic</option>
    <option value="yi">Yiddish</option>
    <option value="lo">Lao</option>
    <option value="uz">Uzbek</option>
    <option value="fo">Faroese</option>
    <option value="ht">Haitian creole</option>
    <option value="ps">Pashto</option>
    <option value="tk">Turkmen</option>
    <option value="nn">Nynorsk</option>
    <option value="mt">Maltese</option>
    <option value="sa">Sanskrit</option>
    <option value="lb">Luxembourgish</option>
    <option value="my">Myanmar</option>
    <option value="bo">Tibetan</option>
    <option value="tl">Tagalog</option>
    <option value="mg">Malagasy</option>
    <option value="as">Assamese</option>
    <option value="tt">Tatar</option>
    <option value="haw">Hawaiian</option>
    <option value="ln">Lingala</option>
    <option value="ha">Hausa</option>
    <option value="ba">Bashkir</option>
    <option value="jw">Javanese</option>
    <option value="su">Sundanese</option>
    <option value="yue">Cantonese</option>
</select>

<div
    class="tooltip"
    data-tip="Whisper will auto-detect language, but selecting may help for smaller clips."
>
    <svg
        class="mx-1"
        width="20px"
        height="20px"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        stroke="#ffffff"
        transform="translate(0, 5)"
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

<button class="btn btn-primary inline-block mr-4" on:click|preventDefault={upload}>Analyze</button
>

<!-- <div class="inline-flex">
<div class="my-auto mr-2">Replace Current Words</div>
<input
type="checkbox"
class="toggle toggle-lg inline-flex"
bind:checked={replaceWordsToMix}
/>
</div> -->



{#if loading}
    <div class="inline-flex h-full align-middle">
        <span class="loading loading-spinner loading-lg"></span>
    </div>
{/if}
<div class="text-sm">Supports audio (wav, mp3) or video (mp4, webm, mov)</div>

<ul class="text-sm">
    <li>To multi drag, click words before dragging.</li>
</ul>

<DraggableZones bind:this={draggableZonesComponent} bind:chosenWords />

<button class="btn btn-primary btn-wide mt-4" on:click={generate}
    >Generate</button
>
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
