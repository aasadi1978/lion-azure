try {
  let targetContainer = document.getElementById('id-statusbar-dragdrop');
  let eventSource = new EventSource('/event-stream-listener');

  let startTime = new Date();
  eventSource.onmessage = function (evt) {
    try {
      let yield_info = JSON.parse(evt.data);

      if (yield_info.popup_message) {
        create_popup(
          (title = 'Notification'),
          (message = yield_info.popup_message),
          'info'
        );
        return;
      }

      if (yield_info.progress_percentage) {
        targetContainer.style.width = yield_info.progress_percentage;
        document.getElementById('id-statusbar-val-dragdrop').innerText =
          ' (' + yield_info.progress_percentage + ')';
      }

      if (yield_info.progress_info) {
        document.getElementById('id-statusbar-info-dragdrop').innerText =
          yield_info.progress_info;
      }

      if (yield_info.progress_percentage == '0%') {
        startTime = new Date();
      }

      let d = new Date() - startTime;
      d /= 1000;
      let total_secnds = Math.round(d);

      if (yield_info.progress_percentage != '100%') {
        document.getElementById('id-time-elapsed-dragdrop').innerText =
          seconds2hm(total_secnds);
      }
    } catch (error) {
      console.error('Error parsing event stream data:', error);
    }
  };
} catch (error) {
  console.error('Error setting up event stream listener:', error);
}
