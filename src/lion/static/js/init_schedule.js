function set_ui_params() {

    // Execute a function when the user releases a key on the keyboard
    document
      .getElementById('id-page-to-form')
      .addEventListener('keyup', function (event) {
        if (event.keyCode === 13) {
          event.preventDefault();
          let v = Number($('#id-page-to-form').val());

          if (Number.isInteger(v)) {
            if (v <= window.n_pages && v > 0) {
              update_page_num(v);
              get_chart_data();
            }
          }
        }
      });

    $(document).ready(function () {
      refresh_options();
    });

    let slider2 = document.getElementById('id-utilisation-double-slider');
    if (slider2 && !slider2.noUiSlider) {
      noUiSlider.create(slider2, {
        start: Array.isArray(window.utilisation_range)
          ? window.utilisation_range.map(Number)
          : [0, 100],
        connect: true,
        range: { min: 0, max: 100 },
      });

      slider2.noUiSlider.on('update', function (values) {
        document.getElementById(
          'id-slider-shift-utilisation-value'
        ).innerText = `Time Utilisation: between ${Math.ceil(
          values[0]
        )}% and ${Math.ceil(values[1])}%`;
      });

      slider2.noUiSlider.on('end', function (values) {
        set_utilisation_slider_range([
          Math.ceil(Number(values[0])),
          Math.ceil(Number(values[1])),
        ]);
      });
    }

  }


// init_schedule.js
function initSchedule() {
  // Parse injected JSON data
  const optionsEl = document.getElementById("options-data");
  if (!optionsEl) {
    console.error("Missing #options-data element — cannot load schedule.");
    return;
  }

  let options;
  try {
    options = JSON.parse(optionsEl.textContent);
  } catch (e) {
    console.error("Failed to parse options JSON:", e);
    return;
  }

  // Expose globally (if needed elsewhere)
  window.options = options;
  window.currPage = options.page_num || 1;
  window.n_pages = options.n_pages || 1;
  window.utilisation_range = options.utilisation_range || [0, 100];

  document.title = options.title || "Driver Schedule";
  window.default_title =  options.title || "Driver Schedule";

  // Initialize your page
  load_available_vehicle_types();
  clear_selected_tours_to_take_action();
  load_available_scenarios();
  load_available_master_plans();
  refresh_tour_string();
  clear_user_changes();
  connection_status();
  set_ui_params();

  // Load initial chart
  get_chart_data(page_num= window.currPage);
}

document.addEventListener("DOMContentLoaded", initSchedule);
