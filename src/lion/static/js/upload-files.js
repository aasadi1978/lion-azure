// /static/js/upload-files.js

document.addEventListener('DOMContentLoaded', () => {
  const uploadBtn2 = document.getElementById('id-1-uploadBtn');
  const fileInput2 = document.getElementById('id-1-fileInput');
  const fileLabel2 = document.getElementById('id-1-fileLabel');

  uploadBtn2.addEventListener('click', () => fileInput2.click());

  function upload_external_file(
    evt,
    allowedExtensions = ['xlsx', 'xlsm', 'csv', 'xls', 'accdb', 'mdb']
  ) {
    const file = evt.target.files[0];
    fileLabel2.textContent = file ? file.name : 'No file selected';

    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('allowedExtensions', JSON.stringify(allowedExtensions));

    fetch('/upload-external-file', {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        create_popup('Uploading file', data.message);
      })
      .catch((error) => {
        console.error('Error uploading file:', error);
        create_popup('Uploading file', 'Failed to upload file.');
      });
  }

  fileInput2.addEventListener('change', (e) => upload_external_file(e));
});
