<script>
    import "../app.css";
</script>



<div class="min-h-screen bg-base-100">
    <div class="navbar bg-base-100 border-b mx-auto max-w-8xl sm:px-6 lg:px-8">
        <div class="logotext text-3xl">SentenceMixer AI</div>

    </div>
    <div class="mx-auto max-w-8xl sm:px-6 lg:px-8">
        <slot />
    </div>
</div>

<style>
    .logotext {
        font-family: 'Audiowide', cursive;
    }
</style>
