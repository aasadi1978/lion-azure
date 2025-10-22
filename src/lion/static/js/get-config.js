async function loadConfig() {
  try {
    const response = await fetch('/static/api_config.json');
    const configData = await response.json();

    if (configData.apiBaseURI.endsWith('/')) {
      configData.apiBaseURI = configData.apiBaseURI.slice(0, -1);
    }

    window.api_config = configData;
  } catch (err) {
    console.error('Failed to load config', err);
  }
}
loadConfig();
