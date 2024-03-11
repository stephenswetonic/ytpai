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
    let fileInputElement;
    let sourceFile;
    let hideVideo = true;
    let dragging = false;
    let rangeSliderComponent;

    // Real start and end values in seconds for slider
    let startTime;
    let endTime;
    let totalDuration;

    onMount(() => {
        videoElement = document.getElementById("sourceVideo");
        fileInputElement = document.getElementById("fileInput");

        fileInputElement.addEventListener("change", function (event) {
            // Will need to allow for audio later
            if (event.target.files[0].type == "video/mp4") {
                error = "";
                sourceFile = event.target.files[0];
                setVideoSource(sourceFile);
            } else {
                error = "Only mp4 is supported";
            }
        });
        loadFFmpeg();
    });

    async function handleDrop(event: DragEvent) {
        dragging = false;
        if (!event.dataTransfer) return;

        if (event.dataTransfer.files.length > 1) {
            error = "Upload 1 file";
        }

        if (event.dataTransfer.files[0].type == "video/mp4") {
            error = "";
            // Will need to allow for audio later
            const [file] = event.dataTransfer.files;
            sourceFile = file;
            setVideoSource(file);
        } else {
            error = "Only mp4 is supported.";
        }
    }

    function setVideoSource(video: File) {
        const fileURL = URL.createObjectURL(video);
        videoElement.src = fileURL;
        hideVideo = false;
    }

    function handleLoadMetaData() {
        if (videoElement) {
            endTime = parseFloat(videoElement.duration);
            totalDuration = parseFloat(videoElement.duration);
            //rangeSliderComponent.updateEndHandle();
        }
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

    async function loadFFmpeg() {
        const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm";
        ffmpeg = new FFmpeg();

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

    async function trimVideo(video: File) {
        state = "convert.start";
        const videoData = await readFile(video);
        await ffmpeg.writeFile("input.mp4", videoData);
        await ffmpeg.exec([
            "-i",
            "input.mp4",
            "-ss",
            "00:00:10",
            "-to",
            "00:00:25",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "output.mp4",
        ]);
        const data = await ffmpeg.readFile("output.mp4");
        state = "convert.done";
        return data as Uint8Array;
    }

    async function convertWebm(video: File) {
        state = "convert.start";
        const videoData = await readFile(video);
        await ffmpeg.writeFile("input.webm", videoData);
        await ffmpeg.exec(["-i", "input.webm", "output.mp4"]);
        const data = await ffmpeg.readFile("output.mp4");
        state = "convert.done";
        return data as Uint8Array;
    }

    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds < 10 ? "0" : ""}${remainingSeconds}`;
    }

    function updateStartHandle(event) {
        //console.log(event.target.value);
        
        rangeSliderComponent.updateStartHandle(event.target.value);
    }

    function updateEndHandle(event) {
        rangeSliderComponent.updateEndHandle(event.target.value);
    }
</script>

<!-- svelte-ignore a11y-media-has-caption -->
<video
    class=" max-w-xl mx-auto mt-2"
    src=""
    id="sourceVideo"
    controls
    hidden={hideVideo}
    on:loadedmetadata={handleLoadMetaData}
></video>

{#if !hideVideo}
    <div class="max-w-xl mx-auto">
        <div class="flex justify-between items-center">
            <!-- First element: RangeSlider -->
            <div class="w-full max-w-full">
                <RangeSlider
                    bind:startTime
                    bind:endTime
                    bind:totalDuration
                    bind:this={rangeSliderComponent}
                />
            </div>

            <input
                type="text"
                class="input input-sm w-10 p-0"
                value={formatTime(startTime)}
                on:change={(event) => updateStartHandle(event)}
            />

            <!-- Second value field -->
            <input
                type="text"
                class="input input-sm w-10 p-0"
                value={formatTime(endTime)}
                on:change={(event) => updateEndHandle(event)}
            />

            <!-- Second element: Trim button -->
            <button class="btn btn-sm btn-primary">Trim</button>
        </div>
    </div>
{/if}

{#if state == "convert.start"}
    <p in:fade>Converting video...</p>
    <div class="progress-bar">
        <div class="progress" style:--progress="{$progress}%">
            {$progress.toFixed(0)}%
        </div>
    </div>
{/if}

<input
    accept="audio/wav, video/mp4"
    id="fileInput"
    type="file"
    style="display: none;"
/>

{#if hideVideo}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-mouse-events-have-key-events -->
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
            ? "dropdrag hover:cursor-pointer"
            : "drop hover:cursor-pointer"}
    >
        {#if state == "loading"}
            <p in:fade>Loading FFmpeg...</p>
        {/if}

        {#if state == "loaded"}
            <p in:fade>Drag video or click here</p>
        {/if}

        {#if error}
            <p in:fade class="error">{error}</p>
        {/if}
    </div>
{/if}

<style>
    .drop {
        width: 600px;
        height: 400px;
        display: grid;
        place-content: center;
        border: 10px dashed hsl(220, 10%, 20%);
    }

    .dropdrag {
        width: 600px;
        height: 400px;
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

    .progress-bar {
        --progress-bar-clr: hsl(180, 100%, 50%);
        --progress-txt-clr: hsl(0, 0%, 0%);

        width: 300px;
        height: 40px;
        position: relative;
        font-weight: 700;
        background-color: hsl(200, 10%, 14%);
        border-radius: 8px;
    }

    .progress-bar .progress {
        width: var(--progress);
        height: 100%;
        position: absolute;
        left: 0px;
        display: grid;
        place-content: center;
        background-color: var(--progress-bar-clr);
        color: var(--progress-txt-clr);
        border-radius: 8px;
    }
</style>
