// src/routes/+page.js
import { _serverStatus } from '../stores/serverStatus';

export async function load() {
    const SERVER_URL = 'https://stag-thankful-buck.ngrok-free.app/';

    const checkServer = async (url, retries = 3, delay = 500) => {
        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(url);
                if (response.ok) {
                    return true; // Server is up
                }
            } catch (error) {
                console.error('Error checking server:', error);
            }
            await new Promise(resolve => setTimeout(resolve, delay)); // Wait before retrying
        }
        return false; // Server is down
    };

    const isServerUp = await checkServer(SERVER_URL);
    _serverStatus.set(isServerUp ? 'up' : 'down');

    return {
        props: {
            _serverStatus: isServerUp ? 'up' : 'down'
        }
    };
}
