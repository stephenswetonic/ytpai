<!-- RangeSliderCanvas.svelte -->
<script>
    import { onMount } from "svelte";

    let start = 0;
    let end = 100;

    export let startTime;
    export let endTime;
    export let totalDuration;

    $: {
        startTime = totalDuration * (start / 100);
    }
    $: {
        endTime = totalDuration * (end / 100);
    }

    let canvas;
    let ctx;
    let dragging = false;
    let activeHandle = null;

    function timeToSeconds(timeString) {
        const [minutes, seconds] = timeString.split(":").map(Number);
        return minutes * 60 + seconds;
    }

    export function updateEndHandle(formattedTime) {
        endTime = timeToSeconds(formattedTime);
        const endTimePercent = endTime / totalDuration;
        end = endTimePercent * 100;
        drawSlider();
    }

    export function updateStartHandle(formattedTime) {
        startTime = timeToSeconds(formattedTime);
        const startTimePercent = startTime / totalDuration;
        start = startTimePercent * 100;
        drawSlider();
    }

    function drawSlider() {
        canvas.width = canvas.parentElement.clientWidth;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Calculate handle positions
        const startHandleX = (start / 100) * (canvas.width - 20) + 10;
        const endHandleX = (end / 100) * (canvas.width - 20) + 10;

        // Draw gray track covering the whole slider
        ctx.fillStyle = "#333";
        ctx.fillRect(10, canvas.height / 2 - 5, startHandleX - 10, 10);
        ctx.fillRect(
            endHandleX,
            canvas.height / 2 - 5,
            canvas.width - endHandleX - 10,
            10,
        );

        // Draw white track between the handles
        ctx.fillStyle = "#fff";
        ctx.fillRect(
            startHandleX,
            canvas.height / 2 - 5,
            endHandleX - startHandleX,
            10,
        );

        // Draw start handle
        ctx.strokeStyle = "#000"; // Border color
        ctx.lineWidth = 1; // Border width
        ctx.fillStyle = activeHandle === "start" ? "#007bff" : "#666";
        ctx.fillRect(startHandleX - 5, canvas.height / 2 - 20, 10, 40);
        ctx.strokeRect(startHandleX - 5, canvas.height / 2 - 20, 10, 40); // Draw border

        // Draw end handle
        ctx.fillStyle = activeHandle === "end" ? "#007bff" : "#666";
        ctx.fillRect(endHandleX - 5, canvas.height / 2 - 20, 10, 40);
        ctx.strokeRect(endHandleX - 5, canvas.height / 2 - 20, 10, 40); // Draw border
    }

    function handleMouseDown(event) {
        const mouseX = event.clientX - canvas.getBoundingClientRect().left;
        //const mouseY = event.clientY - canvas.getBoundingClientRect().top;

        const startHandleX = (start / 100) * (canvas.width - 20) + 10;
        const endHandleX = (end / 100) * (canvas.width - 20) + 10;

        if (mouseX >= startHandleX - 5 && mouseX <= startHandleX + 5) {
            activeHandle = "start";
            dragging = true;
        } else if (mouseX >= endHandleX - 5 && mouseX <= endHandleX + 5) {
            activeHandle = "end";
            dragging = true;
        }
        window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", handleMouseUp);
    }

    function handleMouseMove(event) {
        if (dragging) {
            const mouseX = event.clientX - canvas.getBoundingClientRect().left;
            let newPosition = Math.min(
                Math.max(mouseX - 10, 0),
                canvas.width - 20,
            );

            if (activeHandle === "start") {
                start = (newPosition / (canvas.width - 20)) * 100;
                if (start > end) end = start;
            } else if (activeHandle === "end") {
                end = (newPosition / (canvas.width - 20)) * 100;
                if (end < start) start = end;
            }
            drawSlider();
        }
    }

    function handleMouseUp() {
        dragging = false;
        activeHandle = null;
        window.removeEventListener("mousemove", handleMouseMove);
        window.removeEventListener("mouseup", handleMouseUp);
    }


    onMount(() => {
        ctx = canvas.getContext("2d");
        drawSlider();
    });
</script>

<canvas
    bind:this={canvas}
    width="100%"
    height="50px"
    style="cursor: pointer;"
    on:mousedown={handleMouseDown}
    on:mousemove={handleMouseMove}
    on:mouseup={handleMouseUp}
></canvas>

<style>
    canvas {
        display: block;
        margin: 20px auto;
        image-rendering: pixelated;
    }
</style>
