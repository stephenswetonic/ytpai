<script>
    import "../app.css";
    import { dev } from '$app/environment';
    import { inject } from '@vercel/analytics';
    import { injectSpeedInsights } from '@vercel/speed-insights/sveltekit';
    import { _serverStatus } from '../stores/serverStatus';
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

<footer class="footer bg-base-300 text-base-content p-4">
    <aside>
      <p>Copyright © {new Date().getFullYear()} - All right reserved. &nbsp;&nbsp;&nbsp; Server Status 
        <span class="dot {$_serverStatus === 'up' ? 'green' : 'red'}"></span></p>
    </aside>
</footer>

<style>
    .logotext {
        font-family: 'Audiowide', cursive;
    }
    .dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-left: 5px;
    }
    .green {
        background-color: #00ff00;
    }
    .red {
        background-color: #ff0000;
    }
</style>
