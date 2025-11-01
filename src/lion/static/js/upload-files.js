function upload_external_file(
  evt,
  allowedExtensions = ['xlsx', 'xlsm', 'csv', 'xls', 'accdb', 'mdb'],
  label_id = undefined
) {
  const file = evt.target.files[0];

  if (label_id) {
    const fileLabel = document.getElementById(label_id);
    fileLabel.textContent = file ? file.name : 'No file chosen';
  }

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
