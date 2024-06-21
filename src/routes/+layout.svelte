<script>
    import "../app.css";
    import { dev } from '$app/environment';
    import { inject } from '@vercel/analytics';
    import { injectSpeedInsights } from '@vercel/speed-insights/sveltekit';
    injectSpeedInsights();
    inject({ mode: dev ? 'development' : 'production' });
</script>

<div class="min-h-screen bg-base-100">
    <div class="navbar bg-base-100 border-b mx-auto max-w-8xl sm:px-6 lg:px-8">
        <a class="logotext btn btn-ghost text-3xl" href="/">SENTENCEMIXER AI</a>
        <a class="btn btn-ghost mx-2 absolute right-0" href="/about">ABOUT</a>
    </div>
    <div class="mx-auto max-w-8xl sm:px-6 lg:px-8">
        <slot />
    </div>
</div>

<div class="layout-footer">

</div>

<style>
    .logotext {
        font-family: 'Audiowide', cursive;
    }
    .layout-footer {
        width: 100%;
        height: 100px;
    }
</style>
