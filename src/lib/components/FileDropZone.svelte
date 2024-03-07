<script lang="ts">
    import type { FFmpeg } from "@ffmpeg/ffmpeg";
    import { tweened } from 'svelte/motion';
    import { fade } from "svelte/transition";

    type State = 'loading' | 'loaded' | 'convert.start' | 'convert.error' | 'convert.done';
    let state: State = 'loading';
    let error = ''
    let ffmpeg: FFmpeg;
    let progress = tweened(0);

    function handleDrop(event: DragEvent) {
        if (!event.dataTransfer) return;

        if (event.dataTransfer.files.length > 1) {
            error = 'Upload 1 file';
        }

        // Can check for file type here
        const [file] = event.dataTransfer.files;
        console.log(file);
        
    }


    $: console.log(state);
</script>

<div
    on:drop|preventDefault={handleDrop}
    on:dragover|preventDefault={() => {}}
    data-state={state}
    class="drop"
>
{#if state == 'loading'}
    <p in:fade>Loading FFmpeg...</p>
{/if}

{#if state == 'loaded'}
    <p in:fade>Drag video here</p>
{/if}

{#if state == 'convert.start'}
    <p in:fade>Converting video...</p>
    <div class="progress-bar">
        <div class="progress" style:--progress='{$progress}%'>
            {$progress.toFixed(0)}%
        </div>
    </div>
{/if}

{#if state == 'convert.done'}
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
</style>