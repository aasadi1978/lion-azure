function connection_status() {
  // Perform a health check to determine connection status
  // Return a promise that resolves to 'OK' or an error message

  return new Promise((resolve, reject) => {
    fetch('/health-check')
      .then((response) => {
        if (!response.ok) {
          reject(`HTTP ${response.status}`);
        } else {
          return response.json();
        }
      })
      .then((data) => {
        if (data.status === 'ok') {
          resolve('OK');
          document.title = '✅ ' + (window.default_title || 'lion');
          window.connection_healthy = true;
        }
        reject(data.status);
      })
      .catch((error) => {
        reject(`Error fetching health check: ${error}`);
        document.title = '❌ ' + (window.default_title || 'lion');
        window.connection_healthy = false;
      });
  });
}

// To use this function, call it with await:
// try {
//   const status = await connection_status();
//   if (status !== 'OK') {
//     // Handle connection error
//   }
// } catch (error) {
//   // error will be the message passed to Reject
//   // This catches actual fetch or network errors
//   console.error('Connection error:', error);
// }
