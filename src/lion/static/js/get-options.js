async function loadOptions() {
  try {
    const res = await fetch('/options');
    const data = await res.json();
    data['api_config'] = window.api_config;
    window.options = data;
    document.dispatchEvent(new Event('optionsLoaded'));
  } catch (err) {
    console.error('Failed to load options', err);
  }
}
loadOptions();
