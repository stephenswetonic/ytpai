<!-- VideoPlayer.svelte -->
<script>
    import { onMount } from 'svelte';
    import videojs from 'video.js';
    import 'video.js/dist/video-js.css';
  
    let player;
  
    onMount(() => {
      // Initialize Video.js player
      player = videojs('my-video', {
        controls: true // Enable default controls
      });
  
      // Cleanup on component destruction
      return () => {
        if (player) {
          player.dispose();
        }
      };
    });
  </script>
  
  <div>
    <!-- svelte-ignore a11y-media-has-caption -->
    <video id="my-video" class="video-js" src="https://sam-app-s3uploadbucket-qkgqfgtltuzq.s3.amazonaws.com/1709666227219.mp4"></video>
  </div>
  