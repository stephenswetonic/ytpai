<script lang="ts">
    import { onMount } from "svelte";
    import { tweened } from "svelte/motion";
    import { fade } from "svelte/transition";
    import { FFmpeg } from "@ffmpeg/ffmpeg";
    import RangeSlider from "$lib/components/RangeSlider.svelte";

    type State =
        | "loading"
        | "loaded"
        | "placed"
        | "convert.start"
        | "convert.error"
        | "convert.done";
    let state: State = "loading";

    let error = "";
    let ffmpeg: FFmpeg;
    let progress = tweened(0);
    let videoElement;
    let audioElement;
    let fileInputElement;

    // The original untrimmed file
    export let sourceFile;
    export let trimmedFile;

    let hideVideo = true;
    let hideAudio = true;
    let dragging = false;
    let rangeSliderComponent;

    // Real start and end values in seconds for slider
    export let startTime;
    export let endTime;
    let totalDuration;

    onMount(() => {
        videoElement = document.getElementById("sourceVideo");
        audioElement = document.getElementById("sourceAudio");
        fileInputElement = document.getElementById("fileInput");

        // Handles click to upload file
        fileInputElement.addEventListener("change", function (event) {
            checkInputFile(event.target.files[0]);
        });
        loadFFmpeg();
    });

    function checkInputFile(file: File) {
        if (
            file.type == "video/mp4" ||
            file.type == "video/webm" ||
            file.type == "video/quicktime"
        ) {
            error = "";
            sourceFile = file;
            trimmedFile = file;
            setVideoSource(file);
        } else if (file.type == "audio/wav" || file.type == "audio/mpeg") {
            error = "";
            sourceFile = file;
            trimmedFile = file;
            setAudioSource(file);
        } else {
            error = "File type not supported.";
        }
    }

    // Handle drag and drop into drop zone
    async function handleDrop(event: DragEvent) {
        dragging = false;
        if (!event.dataTransfer) return;

        if (event.dataTransfer.files.length > 1) {
            error = "Upload 1 file";
        }

        checkInputFile(event.dataTransfer.files[0]);
    }

    // Sets the src attribute of the video element for preview
    function setVideoSource(video: File) {
        const fileURL = URL.createObjectURL(video);
        videoElement.src = fileURL;
        hideVideo = false;
    }

    function setAudioSource(audio: File) {
        const fileUrl = URL.createObjectURL(audio);
        audioElement.src = fileUrl;
        hideAudio = false;
    }

    // Load ffmpeg asm module
    async function loadFFmpeg() {
        const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm";
        ffmpeg = new FFmpeg();

        // Update progress bar
        ffmpeg.on("progress", (event) => {
            $progress = event.progress * 100;
        });

        // ffmpeg.on('log', ({ message }) => {
        //     console.log(message);

        // })

        await ffmpeg.load({
            coreURL: `${baseURL}/ffmpeg-core.js`,
            wasmURL: `${baseURL}/ffmpeg-core.wasm`,
        });
        state = "loaded";
    }

    // Reads a js File into a Uint8Array for ffmpeg
    // Mainly needed to access ffmpeg
    async function readFile(file: File): Promise<Uint8Array> {
        return new Promise((resolve) => {
            const fileReader = new FileReader();

            fileReader.onload = () => {
                const { result } = fileReader;
                if (result instanceof ArrayBuffer) {
                    resolve(new Uint8Array(result));
                }
            };

            fileReader.onerror = () => {
                error = "Could not read file";
            };
            fileReader.readAsArrayBuffer(file);
        });
    }

    // Called by the trim button
    function trimMedia() {
        // Bad way of doing this
        if (!hideVideo) {
            trimSource(".mp4", true);
        } else {
            trimSource(".wav", false);
        }
    }

    // Trims the source media for previewing on the page
    async function trimSource(fileExtension: String, isVideo: boolean) {
        state = "convert.start";
        const videoData = await readFile(sourceFile);
        await ffmpeg.writeFile("input" + fileExtension, videoData);
        await ffmpeg.exec([
            "-ss",
            formatTimeFfmpeg(startTime),
            "-to",
            formatTimeFfmpeg(endTime),
            "-i",
            "input" + fileExtension,
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "output" + fileExtension,
        ]);
        const data = await ffmpeg.readFile("output" + fileExtension);
        const file = new File([data], "output" + fileExtension);
        trimmedFile = file;

        if (isVideo) {
            setVideoSource(file);
        } else {
            setAudioSource(file);
        }
        state = "convert.done";
        progress = tweened(0);
    }

    // Convert duration in seconds to MM:SS
    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds < 10 ? "0" : ""}${remainingSeconds}`;
    }

    // Calculate hours, minutes, and remaining seconds for ffmpeg
    function formatTimeFfmpeg(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const roundedSeconds = Math.round(seconds % 60); // Round the seconds
        const paddedHours = hours.toString().padStart(2, "0");
        const paddedMinutes = minutes.toString().padStart(2, "0");
        const paddedSeconds = roundedSeconds.toString().padStart(2, "0"); // Pad and round the seconds

        // Construct the time format HH:MM:SS
        return `${paddedHours}:${paddedMinutes}:${paddedSeconds}`;
    }

    // Called when video/audio element finishes loading
    function handleLoadMetaData(htmlMediaElement) {
        // If htmlElement is showing and totalDuration not set
        // If totalduration is set, we don't want to set again
        if (htmlMediaElement) {
            totalDuration = parseFloat(htmlMediaElement.duration);
        }
    }

    function closeVideo() {
        videoElement.src = "";
        hideVideo = true;
        fileInputElement.value = "";
    }

    function closeAudio() {
        audioElement.src = "";
        hideAudio = true;
        fileInputElement.value = "";
    }

    function handleClick() {
        fileInputElement.click();
    }

    function handleDragenter() {
        dragging = true;
    }

    function handleDragleave() {
        dragging = false;
    }

    function handleMouseover() {
        dragging = true;
    }

    function handleMouseleave() {
        dragging = false;
    }

    function updateStartHandle(event) {
        rangeSliderComponent.updateStartHandle(event.target.value);
    }

    function updateEndHandle(event) {
        rangeSliderComponent.updateEndHandle(event.target.value);
    }
</script>

<div class="relative max-w-xl mt-2 mx-auto flex items-center justify-between">
    <!-- Video Element -->
    <!-- svelte-ignore a11y-media-has-caption -->
    <video
        src=""
        id="sourceVideo"
        controls
        class="w-full"
        hidden={hideVideo}
        on:loadedmetadata={() => handleLoadMetaData(videoElement)}
    ></video>

    <!-- Audio Element -->
    <audio
        src=""
        id="sourceAudio"
        controls
        class="w-full"
        hidden={hideAudio}
        on:loadedmetadata={() => handleLoadMetaData(audioElement)}
    ></audio>

    {#if !hideVideo }
        <!-- Close button for Video Element -->
        <button class="btn btn-ghost btn-sm absolute top-0 right-0 mt-2 mr-2 z-10"
                on:click={closeVideo}
        >
            <svg
                width="20px"
                height="20px"
                viewBox="0 0 512 512"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path
                    d="M443.6,387.1L312.4,255.4l131.5-130c5.4-5.4,5.4-14.2,0-19.6l-37.4-37.6c-2.6-2.6-6.1-4-9.8-4c-3.7,0-7.2,1.5-9.8,4  L256,197.8L124.9,68.3c-2.6-2.6-6.1-4-9.8-4c-3.7,0-7.2,1.5-9.8,4L68,105.9c-5.4,5.4-5.4,14.2,0,19.6l131.5,130L68.4,387.1  c-2.6,2.6-4.1,6.1-4.1,9.8c0,3.7,1.4,7.2,4.1,9.8l37.4,37.6c2.7,2.7,6.2,4.1,9.8,4.1c3.5,0,7.1-1.3,9.8-4.1L256,313.1l130.7,131.1  c2.7,2.7,6.2,4.1,9.8,4.1c3.5,0,7.1-1.3,9.8-4.1l37.4-37.6c2.6-2.6,4.1-6.1,4.1-9.8C447.7,393.2,446.2,389.7,443.6,387.1z"
                    fill="#ff0000"
                />
            </svg>
        </button>
    {/if}

    {#if !hideAudio}
        <!-- Close button for Audio Element -->
        <button class="btn btn-ghost btn-sm z-10"
                style="margin-right: 10px;"
                on:click={closeAudio}
        >
            <svg
                width="20px"
                height="20px"
                viewBox="0 0 512 512"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path
                    d="M443.6,387.1L312.4,255.4l131.5-130c5.4-5.4,5.4-14.2,0-19.6l-37.4-37.6c-2.6-2.6-6.1-4-9.8-4c-3.7,0-7.2,1.5-9.8,4  L256,197.8L124.9,68.3c-2.6-2.6-6.1-4-9.8-4c-3.7,0-7.2,1.5-9.8,4L68,105.9c-5.4,5.4-5.4,14.2,0,19.6l131.5,130L68.4,387.1  c-2.6,2.6-4.1,6.1-4.1,9.8c0,3.7,1.4,7.2,4.1,9.8l37.4,37.6c2.7,2.7,6.2,4.1,9.8,4.1c3.5,0,7.1-1.3,9.8-4.1L256,313.1l130.7,131.1  c2.7,2.7,6.2,4.1,9.8,4.1c3.5,0,7.1-1.3,9.8-4.1l37.4-37.6c2.6-2.6,4.1-6.1,4.1-9.8C447.7,393.2,446.2,389.7,443.6,387.1z"
                    fill="#ff0000"
                />
            </svg>
        </button>
    {/if}

</div>






{#if !hideVideo || !hideAudio}
    <div class="max-w-xl mx-auto">
        <div class="flex justify-between items-center">
            <div class="w-full max-w-full">
                <RangeSlider
                    bind:startTime
                    bind:endTime
                    bind:totalDuration
                    bind:this={rangeSliderComponent}
                />
            </div>

            <!-- Start value field -->
            <label class="input input-bordered flex items-center gap-2 p-1">
                Start
                <input
                    type="text"
                    class="grow w-12 p-1"
                    placeholder="Start Time"
                    value={formatTime(startTime)}
                    on:change={(event) => updateStartHandle(event)}
                />
            </label>

            <!-- End value field -->
            <label class="input input-bordered flex items-center gap-2 p-1">
                End
                <input
                    type="text"
                    class="grow w-12 p-1"
                    placeholder="End Time"
                    value={formatTime(endTime)}
                    on:change={(event) => updateEndHandle(event)}
                />
            </label>

            <!-- Trim button -->
            <button
                class="btn btn-sm btn-primary ml-1"
                on:click={trimMedia}
                data-tooltip="Trim media to selected duration">Trim</button
            >
        </div>
    </div>
{/if}

{#if state == "convert.start"}
    <div class="container">
        <div class="text-container">
            <p id="processing-text">Processing...</p>
        </div>
        <div class="progress-bar">
            <div class="progress" style:--progress="{$progress}%">
                {$progress.toFixed(0)}%
            </div>
        </div>
    </div>
{/if}

<input
    accept="audio/wav, audio/mpeg, video/mp4, video/webm, video/quicktime"
    id="fileInput"
    type="file"
    style="display: none;"
/>

{#if hideVideo && hideAudio}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-mouse-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div
        on:drop|preventDefault={handleDrop}
        on:dragenter={handleDragenter}
        on:dragleave={handleDragleave}
        on:mouseover={handleMouseover}
        on:mouseleave={handleMouseleave}
        on:click={handleClick}
        on:dragover|preventDefault={() => {}}
        data-state={state}
        class={dragging
            ? "dropdrag hover:cursor-pointer my-2"
            : "drop hover:cursor-pointer my-2"}
    >
        {#if state == "loading"}
            <p in:fade>Loading FFmpeg...</p>
        {/if}

        {#if state == "loaded"}
            <p in:fade>Drag file or click here</p>
        {/if}

        {#if error}
            <p in:fade class="error">{error}</p>
        {/if}
    </div>
{/if}

<style>
    .drop {
        margin-left: auto;
        margin-right: auto;
        height: 200px;
        display: grid;
        place-content: center;
        border: 10px dashed hsl(220, 10%, 20%);
    }

    .dropdrag {
        margin-left: auto;
        margin-right: auto;
        height: 200px;
        display: grid;
        place-content: center;
        border: 10px dashed hsl(222, 22%, 67%);
    }

    .drop p {
        text-align: center;
    }

    .error {
        color: red;
    }

    .container {
        width: 300px;
        margin: 0 auto;
    }
    .text-container {
        margin-bottom: 2px; /* Adjust margin between text and progress bar */
    }

    #processing-text {
        margin: 0; /* Remove default margin */
    }

    .progress-bar {
        --progress-bar-clr: hsl(180, 100%, 50%);
        --progress-txt-clr: hsl(0, 0%, 0%);
        width: 300px;
        height: 40px;
        font-weight: 700;
        background-color: hsl(200, 10%, 14%);
        border-radius: 8px;
    }

    .progress-bar .progress {
        width: var(--progress);
        height: 100%;
        background-color: var(--progress-bar-clr);
        color: var(--progress-txt-clr);
        border-radius: 8px;
    }
</style>
