let previous_message = 'OK';

function startHealthCheck() {
  let statusInfo = document.getElementById('id-statusbar-info-dragdrop');
  let healthIcon = document.getElementById('id-connection-health-icon');

  async function checkHealth() {
    try {
      const response = await fetch('/health-check');

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'ok') {
        // Connected and healthy
        statusInfo.innerText = 'Connected';
        statusInfo.style.color = '#13e3ceff';
        statusInfo.style.fontWeight = 'bold';
        statusInfo.style.fontSize = '1.2em';
        if (healthIcon) healthIcon.textContent = '✅';

        // If previously disconnected, perform reload
        if (previous_message !== 'OK') {
          statusInfo.innerText =
            'Reconnected - Reloading data. Please wait ...';
          const reload_status = await sync_post('/cold-schedule-reload/', {});
          if (reload_status.code === 400) {
            throw new Error(`HTTP ${reload_status.error}`);
          }
        }
        statusInfo.innerText = 'Connected.';
        document.title = '✅ ' + (window.default_title || 'LION');
        window.connection_healthy = true;
      } else {
        throw new Error('Invalid response payload');
      }
    } catch (err) {
      // Connection lost or invalid response
      statusInfo.innerText = 'Connection lost. Retrying...';
      statusInfo.style.color = 'red';
      statusInfo.style.fontWeight = 'bold';
      statusInfo.style.fontSize = '1.2em';
      if (healthIcon) healthIcon.textContent = '❌';
      previous_message = 'Connection lost';
      console.warn('Health check failed:', err);
      document.title = '❌ ' + (window.default_title || 'LION');
      window.connection_healthy = false;
    }
  }

  // run immediately, then every 10s
  checkHealth();
  setInterval(checkHealth, 10000);
}

window.addEventListener('load', startHealthCheck);
