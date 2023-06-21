<script>
    import "../app.css";
</script>



<div class="min-h-screen bg-base-100">
    <div class="navbar bg-base-100 border-b mx-auto max-w-8xl sm:px-6 lg:px-8">
        <a class="logotext btn btn-ghost text-3xl" href="/">SentenceMixer AI</a>
        <a class="btn btn-ghost mx-2 absolute right-0" href="/about">About</a>
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
