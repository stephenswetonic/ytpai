<!-- Toast.svelte -->
<script>
    import { onDestroy } from 'svelte';
    import { fade } from 'svelte/transition';
  
    export let messages = [];
    export let duration = 3000; // Default duration for the toast to be visible
  
    onDestroy(() => {
      clearTimeout(hideTimeout);
    });
  
    const hideTimeout = setTimeout(() => {
      messages.shift(); // Remove the oldest message from the stack
    }, duration);
  </script>
  
  {#each messages as message, index}
    <div class="toast" transition:fade>
      <div class="toast-message">{message}</div>
    </div>
  {/each}
  
  <style>
    .toast {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background-color: #333;
      color: #fff;
      padding: 10px 20px;
      border-radius: 5px;
      box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.3);
      z-index: 1000;
      margin-bottom: 10px;
    }
  
    .toast-message {
      font-size: 14px;
    }
  </style>
  