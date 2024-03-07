<script lang="ts">
    //import type { FFmpeg } from "@ffmpeg/ffmpeg";
    import { onMount } from "svelte";
    import { tweened } from "svelte/motion";
    import { fade } from "svelte/transition";
    import { FFmpeg } from "@ffmpeg/ffmpeg";
    //import { writable } from 'svelte/store';

    type State =
        | "loading"
        | "loaded"
        | "convert.start"
        | "convert.error"
        | "convert.done";
    let state: State = "loading";
    let error = "";
    let ffmpeg: FFmpeg;
    let progress = tweened(0);

    onMount(() => {
        loadFFmpeg();
    })

    async function handleDrop(event: DragEvent) {
        if (!event.dataTransfer) return;

        if (event.dataTransfer.files.length > 1) {
            error = "Upload 1 file";
        }
        //debugger;
        // Can check for file type here
        if (event.dataTransfer.files[0].type == "video/webm") {
            error = '';
            const [file] = event.dataTransfer.files;
            const data = await convertWebm(file);
        } else {
            error = 'Only webm is supported.'
        }
        
    }

    async function loadFFmpeg() {
        const baseURL = "https://unpkg.com/@ffmpeg/core-mt@0.12.6/dist/esm";
        ffmpeg = new FFmpeg();

        ffmpeg.on('progress', event => {
            $progress = event.progress * 100;
        });

        // ffmpeg.on('log', ({ message }) => {
        //     console.log(message);
            
        // })

        await ffmpeg.load({
            coreURL: `${baseURL}/ffmpeg-core.js`,
            wasmURL: `${baseURL}/ffmpeg-core.wasm`,
            workerURL: `${baseURL}/ffmpeg-core.worker.js`
        });
        state = 'loaded';
        console.log("ffmpeg loaded");
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
                error = 'Could not read file';
            };
            fileReader.readAsArrayBuffer(file);
        });
    }

    async function trimVideo(video: File) {
        state = 'convert.start';
        const videoData = await readFile(video);
        await ffmpeg.writeFile("input.mp4", videoData);
        await ffmpeg.exec(['-i', 'input.mp4', '-ss', '00:00:10', '-to', '00:00:25', '-c:v', 'copy', '-c:a', 'copy', 'output.mp4']);
        const data = await ffmpeg.readFile('output.mp4');
        state = 'convert.done';
        return data as Uint8Array;
    }

    async function convertWebm(video: File) {
        state = 'convert.start';
        const videoData = await readFile(video);
        await ffmpeg.writeFile("input.webm", videoData);
        await ffmpeg.exec(['-i', 'input.webm', 'output.mp4']);
        const data = await ffmpeg.readFile('output.mp4');
        state = 'convert.done';
        return data as Uint8Array;
    }

    $: console.log(state);
</script>

<div
    on:drop|preventDefault={handleDrop}
    on:dragover|preventDefault={() => {}}
    data-state={state}
    class="drop"
>
    {#if state == "loading"}
        <p in:fade>Loading FFmpeg...</p>
    {/if}

    {#if state == "loaded"}
        <p in:fade>Drag video here</p>
    {/if}

    {#if state == "convert.start"}
        <p in:fade>Converting video...</p>
        <div class="progress-bar">
            <div class="progress" style:--progress="{$progress}%">
                {$progress.toFixed(0)}%
            </div>
        </div>
    {/if}

    {#if state == "convert.done"}
        <p in:fade>Done</p>
    {/if}

    {#if error}
        <p in:fade class="error">{error}</p>
    {/if}
</div>

<style>
    .drop {
        width: 600px;
        height: 400px;
        display: grid;
        place-content: center;
        border: 10px dashed hsl(220, 10%, 20%);

    }

    .drop p {
        text-align: center;

    }

    .drop p .error {
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
