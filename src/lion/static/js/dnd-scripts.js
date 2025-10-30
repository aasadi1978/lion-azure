function load_chart_on_full_page_load(chart_data) {
  if (chart_data != undefined) {
    load_driver_shift_chart((dct_chart_data = chart_data));
  }

  window.location.href = '/';

}

function update_page_num(pagenum) {
  window.currPage = Number(pagenum);
  document.getElementById('id-page-to-form').value = window.currPage;

  let page_status = sync_post(
    '/update-page-number',
    (dct_params = { page_num: window.currPage })
  );
  if (page_status.code != 200) {
    create_popup(
      (message = page_status.message),
      (title = 'Error updating page')
    );
  }
}

function clear_user_changes() {
  window.dct_user_changes = {
    dct_timechanges: {},
    dct_shiftchanges: {},
    deletedshifts: [],
  };
  window.selected_movements_to_take_action = [];
  window.selected_tours_to_take_action = [];

  py2js(
    (str_func_name = 'clear_user_changes'),
    (dct_params = {}),
    (url = '/drivers')
  );
}

function get_chart_data() {
  let get_chart_data_status = sync_post('/get-chart-data', (dct_params = {}));

  build_schedule_gantt_chart();
  load_driver_shift_chart((dct_chart_data = get_chart_data_status));
  scrollIntoDiv((getElementById = 'id-all_maps'));
}

// function get_utilisation_slider_range() {

//   let status_get_utilisation_slider_range = py2js(
//     (str_func_name = 'get_utilisation_slider_range'),
//     (dct_params = {}),
//     (url = '/drivers')
//   );

//   set_utilisation_slider(
//     utilisation_range=status_get_utilisation_slider_range.range)
// };

function set_utilisation_slider_range(utilisation_range = [0, 100]) {
  let status_set_utilisation_range = py2js(
    (str_func_name = 'set_utilisation_slider_range'),
    (dct_params = { range: utilisation_range }),
    (url = '/drivers')
  );

  if (status_set_utilisation_range.status != '') {
    alert(status_set_utilisation_range.status);
  }
}

function load_available_scenarios() {
  // $("#id-scn-dropdown").empty();
  // $("#id-tmp-master-plan-dropdown").empty();

  let status_load_available_scenarios = py2js(
    (str_func_name = 'load_available_scenarios'),
    (dct_params = {}),
    (url = '/drivers')
  );

  // let scenarios = status_load_available_scenarios['scenarios']
  // let tmpMasterPlans = status_load_available_scenarios['tmp_masterplans']
  // let select = document.getElementById("id-scn-dropdown");

  // for (var i = 0; i < scenarios.length; i++) {
  //   var opt = scenarios[i];
  //   var el = document.createElement("option");
  //   el.textContent = opt;
  //   el.value = opt;
  //   el.style.fontFamily = 'FedEx Sans Xbold'
  //   el.style.fontSize = '18px'
  //   el.id = 'id-scn-' + i
  //   select.appendChild(el);
  // }

  // load_available_temp_master_plans()
}

// function load_available_temp_master_plans() {

//   $("#id-tmp-master-plan-dropdown").empty();

//   let dct_timestamps = py2js(
//     (str_func_name = 'load_available_scenarios'),
//     (dct_params = { 'tempMasterPlan': true }),
//     (url = '/drivers')
//   );

//   let tmptimestamps = Object.keys(dct_timestamps)
//   let select2 = document.getElementById("id-tmp-master-plan-dropdown");

//   for (var i = 0; i < tmptimestamps.length; i++) {
//     var opt = tmptimestamps[i];
//     var el = document.createElement("option");
//     el.textContent = opt;
//     el.value = tmptimestamps[opt];
//     el.style.fontFamily = 'FedEx Sans'
//     el.style.fontSize = '18px'
//     el.id = 'id-master-plan-temp-' + i
//     select2.appendChild(el);
//   }

// };

function load_available_master_plans() {
  $('#id-master-plan-dropdown').empty();

  let status_load_available_scenarios2 = py2js(
    (str_func_name = 'load_available_scenarios'),
    (dct_params = { load_master_plans: true }),
    (url = '/drivers')
  );

  let scenarios = status_load_available_scenarios2['scenarios'];
  let select = document.getElementById('id-master-plan-dropdown');

  for (var i = 0; i < scenarios.length; i++) {
    var opt = scenarios[i];
    var el = document.createElement('option');
    el.textContent = opt;
    el.value = opt;
    el.id = 'id-plan-' + i;
    el.style.fontFamily = 'FedEx Sans';
    el.style.fontSize = '18px';
    select.appendChild(el);
  }
}

function load_available_vehicle_types() {
  let dct_vehicle = py2js(
    (str_func_name = 'load_available_vehicle_types'),
    (dct_params = {}),
    (url = '/drivers')
  );

  let vehicle_codes = Object.keys(dct_vehicle);

  $('#id-movement-vehicle-type').empty();
  let select_obj = document.getElementById('id-movement-vehicle-type');
  for (var i = 0; i < vehicle_codes.length; i++) {
    var vcode = vehicle_codes[i];
    var el = document.createElement('option');
    el.textContent = dct_vehicle[vcode];
    el.value = vcode;
    el.id = 'id-vehicle-' + i;
    el.style.fontFamily = 'FedEx Sans';
    el.style.fontSize = '16px';
    select_obj.appendChild(el);
  }

  $('#id-shift-vehicle-type').empty();
  select_obj = document.getElementById('id-shift-vehicle-type');
  for (var i = 0; i < vehicle_codes.length; i++) {
    var vcode = vehicle_codes[i];
    var el = document.createElement('option');
    el.textContent = dct_vehicle[vcode];
    el.value = vcode;
    el.id = 'id-vehicle-' + i;
    el.style.fontFamily = 'FedEx Sans';
    el.style.fontSize = '16px';
    select_obj.appendChild(el);
  }

  $('#id-search-by-vehicle').empty();
  select_obj = document.getElementById('id-search-by-vehicle');
  for (var i = 0; i < vehicle_codes.length; i++) {
    var vcode = vehicle_codes[i];
    var el = document.createElement('option');
    el.textContent = dct_vehicle[vcode];
    el.value = vcode;
    el.id = 'id-vehicle-' + i;
    el.style.fontFamily = 'FedEx Sans';
    el.style.fontSize = '16px';
    select_obj.appendChild(el);
  }

  $('#id-mov-vehicle-type-modify').empty();
  select_obj = document.getElementById('id-mov-vehicle-type-modify');
  for (var i = 0; i < vehicle_codes.length; i++) {
    var vcode = vehicle_codes[i];
    var el = document.createElement('option');
    el.textContent = dct_vehicle[vcode];
    el.value = vcode;
    el.id = 'id-vehicle-' + i;
    el.style.fontFamily = 'FedEx Sans';
    el.style.fontSize = '16px';
    select_obj.appendChild(el);
  }
}

function refresh_unplanned_movs() {
  $('#id-movement-bucket').empty();

  let dct_unplanned_movements = py2js(
    (str_func_name = 'refresh_unplanned_movs'),
    (dct_params = {}),
    (url = '/drivers')
  );

  __list_movs = Object.keys(dct_unplanned_movements);

  let __selected_movs = document.getElementById('id-movement-bucket');
  let _n_unplanned_movs = __list_movs.length;

  for (let i = 0; i < _n_unplanned_movs; i++) {
    let mid = __list_movs[i];
    let locStr = dct_unplanned_movements[mid];
    let el = document.createElement('option');
    el.textContent = locStr;
    el.value = mid;
    el.style.fontSize = '1.05em';
    __selected_movs.appendChild(el);
  }

  $('#id-movement-bucket').selectpicker('refresh');

  document.getElementById('id-lbl-num-unplanned-movs').innerText =
    'Unplnd (' + _n_unplanned_movs + ')';

  // __selected_movs.title = 'Unplnd (' + _n_unplanned_movs + ')'
}

function refresh_tour_string() {
  let __refresh_tour_string = py2js(
    (str_func_name = 'refresh_tour_string'),
    (dct_params = {}),
    (url = '/drivers')
  );

  let dct_loc_string = __refresh_tour_string.dct_loc_string;
  // let __selected_shifts = __refresh_tour_string.selected_shifts
  // let __selected_chgo = __refresh_tour_string.selected_co
  // let __selected_vehicles = __refresh_tour_string.selected_vehicles
  // __dct_co = __refresh_tour_string.dct_co
  // __chgovers = Object.keys(__refresh_tour_string.dct_co)
  let list_changeovers = __refresh_tour_string.list_changeovers;
  let list_wkdays = __refresh_tour_string.selected_weekdays;

  if (list_wkdays.length > 0) {
    for (let dy of list_wkdays) {
      let dyLower = dy.toLowerCase();
      let checkboxId = `id-enable-${dyLower}-data`;

      let checkbox = document.getElementById(checkboxId);

      if (checkbox && !checkbox.checked) {
        checkbox.click();
      }
    }
  }

  __dct_unplanned_movements = Object.keys(
    __refresh_tour_string.dct_unplanned_movements
  );
  __list_movs = Object.keys(__refresh_tour_string.dct_unplanned_movements);

  $('#id-shift-string').empty();
  $('#id-changeovers').empty();

  refresh_unplanned_movs();

  let driver_lanes = Object.keys(dct_loc_string);

  let __selected_drivers = document.getElementById('id-shift-string');
  for (let i = 0; i < driver_lanes.length; i++) {
    let lane = driver_lanes[i];
    let el = document.createElement('option');
    el.textContent = lane;
    el.value = dct_loc_string[lane];
    el.style.fontSize = '1.05em';
    __selected_drivers.appendChild(el);
  }

  let __selected_co = document.getElementById('id-changeovers');
  for (let i = 0; i < list_changeovers.length; i++) {
    let c = list_changeovers[i];
    let el = document.createElement('option');
    // el.textContent = __refresh_tour_string.dct_co[c];
    el.textContent = c;
    el.value = list_changeovers[i];
    el.style.fontSize = '1.05em';
    __selected_co.appendChild(el);
  }

  // if (__selected_chgo.length > 0) {
  //   for (let i = 0; i < __selected_co.length; i++) {
  //     __selected_co.options[i].selected = __selected_chgo.indexOf(__selected_co.options[i].value) >= 0;
  //   };
  //   $("#id-changeovers option:selected").prependTo("#id-changeovers");
  // };

  // if (__selected_vehicles.length > 0) {
  //   for (let i = 0; i < __selected_vehicles.length; i++) {
  //     selectElement(id = 'id-search-by-vehicle', valueToSelect = __selected_vehicles[i].toString())
  //   };
  // }
}

function un_hide_slider() {
  let x = document.getElementById('id-tour-utilisation-bar');
  if (x.style.display == 'block') {
    document.getElementById('id-tour-utilisation-bar').style.display = 'none';
  } else {
    document.getElementById('id-tour-utilisation-bar').style.display = 'block';
  }
}

function toggle_zoom() {
  py2js(
    (str_func_name = 'toggle_zoom'),
    (dct_params = {
      zoom_on: document.getElementById('id-enable-zoom-switch').checked,
    }),
    (url = '/drivers')
  );
}

function update_suppliers() {
  set_title('Updating suppliers ...');
  let status_update_suppliers = py2js(
    (str_func_name = 'update_suppliers'),
    (dct_params = {}),
    (url = '/drivers')
  );
  set_default_title();

  if (status_update_suppliers.hasOwnProperty('err')) {
    create_popup(
      (title = 'Updating suppliers failed'),
      (message = status_update_suppliers.err)
    );
    return;
  }
  window.location.href = '/loading_schedule/';
}

function refresh_options(opts = undefined) {
  if (opts != undefined) {
    options = opts;
  }

  // Check if options is defined, if not return early
  if (options === undefined) {
    console.warn('options variable is not defined');
    return;
  }

  n_pages = options.n_pages;
  n_all_drivers = options.n_all_drivers;
  n_drivers = options.n_drivers;
  weekday = options.weekday;
  let enbl_log = options.enable_logging;
  let traffic_type = options.traffic_type;
  let enbl_zoom = options.enbl_zoom;

  if (
    !(document.getElementById('id-enable-logging-switch').checked == enbl_log)
  ) {
    document.getElementById('id-enable-logging-switch').click();
  }

  if (
    !(document.getElementById('id-enable-zoom-switch').checked == enbl_zoom)
  ) {
    document.getElementById('id-enable-zoom-switch').click();
  }

  update_page_num(options.page_num);
  // selectElement('id-week-day', weekday);
  selectElement('id-page-size-dropdown', options.page_size);
  selectElement('id-week-day-for-movement', weekday);
  selectElement('id-mov-traffic-type', traffic_type);
  set_default_title();

  document.getElementById('id-basket-btn').innerHTML =
    '<i class="tim-icons icon-cart"></i> My Basket' +
    ' (' +
    options.basket_drivers.length +
    ')';
}

function set_default_title(opts = undefined) {
  if (opts != undefined) {
    window.default_title = opts.title;
  }

  if (window.connection_healthy === false) {
    document.title = '❌ ' + (window.default_title || 'lion');
  } else {
    document.title = '✅ ' + (window.default_title || 'lion');
  }
}

function set_title(txt = '') {
  document.title = txt;
}

function set_busy_title() {
  document.title = 'Busy ...';
}

function insert_loc_into_mov_loc_string() {
  // let __join_str = '\u00A0\u00A0->\u00A0\u00A0'
  let frm = document.getElementById('id-movement-loc-string').value;
  let __loc = $('#id-loc-lookup-list').val();

  if (frm == '') {
    document.getElementById('id-movement-loc-string').value = __loc;
  } else {
    document.getElementById('id-movement-loc-string').value =
      frm + window.loc_string_spliter + __loc;
  }
}

function load_changeover_shifts(changeovers = []) {
  let changeover_schedule_status = sync_post(
    '/load-changeover-shifts',
    (dct_params = { changeovers: changeovers })
  );

  if (changeover_schedule_status.code === 200) {
    load_driver_shift_chart(
      (dct_chart_data = changeover_schedule_status.chart_data)
    );
  }

  if (changeover_schedule_status.code === 400) {
    create_popup(
      (title = 'Loading changeover schedule'),
      (message = changeover_schedule_status.error),
      (type = 'error')
    );
  }
}

function load_weekday_filtered_shifts(day = '') {
  let weekday_schedule_status = sync_post(
    '/load-weekday-schedule',
    (dct_params = { weekday: day })
  );

  if (weekday_schedule_status.code === 200) {
    load_driver_shift_chart(
      (dct_chart_data = weekday_schedule_status.chart_data)
    );
  }

  if (weekday_schedule_status.code === 201) {
    window.location.href = '/loading_schedule/';
  }

  if (weekday_schedule_status.code === 400) {
    create_popup(
      (title = 'Loading weekday schedule'),
      (message = weekday_schedule_status.error),
      (type = 'error')
    );
  }
}

function load_my_basket_data() {
  let bskt_status = sync_post('/load-basket', (dct_params = {}));

  if (bskt_status.code === 200) {
    load_driver_shift_chart((dct_chart_data = bskt_status.chart_data));
  }

  if (bskt_status.code === 201) {
    // create_popup(
    //   (title = 'Basket is empty'),
    //   (message = 'Please add drivers to your basket before loading.'),
    //   (type = 'info')
    // );
    load_driver_shift_chart((dct_chart_data = {}));
    return;
  }

  if (bskt_status.code === 400) {
    create_popup(
      (title = 'Loading basket data'),
      (message = bskt_status.error),
      (type = 'error')
    );
    set_default_title();
    return;
  }
}

function save_filter_params(dctparams_data = {}) {
  return sync_post('/refresh-schedule-filter', (dct_params = dctparams_data));
}

function build_schedule_gantt_chart(page_size = undefined) {
  if (page_size === undefined) {
    if (options) {
      page_size = options.page_size;
    } else {
      page_size = 15;
    }
  }

  // let h = Math.min(options.n_drivers + 5, page_size) * 6.5
  let h = page_size * 6.5;
  hvh = h.toString() + 'vh';
  let w = '97vw';

  // if (document.getElementById('id-remove-map').checked) {
  //   w = '97vw';
  // } else {
  //   w = '77vw';
  // }

  let toursMap = document.getElementById('tours_map');
  if (toursMap) toursMap.remove();

  let allMapsDiv = document.getElementById('id-all_maps');

  let full_disp_div = document.getElementById('id-disp-drag-full');
  if (!full_disp_div) {
    full_disp_div = document.createElement('div');
    full_disp_div.id = 'id-disp-drag-full';
    allMapsDiv.append(full_disp_div);
  }

  let chartAssignDriversDouble = document.getElementById('id-disp-drag-double');
  if (chartAssignDriversDouble) chartAssignDriversDouble.remove();

  let parentChartAssignDrivers = document.getElementById(
    'parent-chart-assign-drivers'
  );
  if (!parentChartAssignDrivers) {
    parentChartAssignDrivers = document.createElement('div');
    parentChartAssignDrivers.id = 'parent-chart-assign-drivers';
    full_disp_div.append(parentChartAssignDrivers);
  }

  let chartAssignDrivers = document.getElementById('chart-assign-drivers');
  if (chartAssignDrivers) chartAssignDrivers.remove();

  let newDiv = document.createElement('div');
  newDiv.id = 'chart-assign-drivers';
  newDiv.style.width = w;
  newDiv.style.height = hvh;
  newDiv.style.overflow = 'auto';
  parentChartAssignDrivers.appendChild(newDiv);

  build_tour_desc_div();
}

function build_tour_desc_div(parent_div_id = 'id-disp-drag-full') {
  let page_size = 15;
  if (window.options) {
    page_size = options.page_size;
  }

  let descOuterDiv = document.getElementById('id-tour-desc-container');
  if (descOuterDiv) descOuterDiv.remove();

  let parentDiv = document.getElementById(parent_div_id);
  if (!parentDiv) {
    parentDiv = document.createElement('div');
    parentDiv.id = parent_div_id;
  }

  descOuterDiv = document.createElement('div');
  descOuterDiv.id = 'id-tour-desc-container';
  descOuterDiv.className = 'col-lg-15';
  descOuterDiv.style.width = '100vw';
  descOuterDiv.style.height = '23vh';
  // descOuterDiv.style.border = "1px solid black";
  descOuterDiv.style.overflow = 'auto';

  if (page_size > 20) {
    descOuterDiv.style.position = 'fixed';
    descOuterDiv.style.top = '80%';
  }

  let innerDiv = document.createElement('div');
  if (innerDiv) innerDiv.remove();
  innerDiv.className = 'col-lg-13';
  innerDiv.id = 'id-shift-information-label-parent';
  innerDiv.style.display = 'none';
  innerDiv.style.width = '96.97vw';
  innerDiv.style.overflow = 'auto';
  descOuterDiv.appendChild(innerDiv);

  parentDiv.appendChild(descOuterDiv);

  let label = document.createElement('label');
  label.className = 'card-body col-form-label';
  label.id = 'id-shift-information-label';
  label.style.fontSize = '1.3em';
  label.style.width = '96.97vw';
  label.style.height = '20vh';
  label.style.justifySelf = 'start';
  // label.style.backgroundColor = 'white';
  label.style.backgroundColor = '#F5F5DC';
  label.style.color = 'black';
  innerDiv.appendChild(label);
}


function insert_disp_drag_double() {
  let tmpDiv = document.getElementById('id-tour-desc-container');
  if (tmpDiv) tmpDiv.remove();

  let tmpDiv2 = document.getElementById('id-disp-drag-double');
  if (tmpDiv2) tmpDiv2.remove();

  let tmpDiv3 = document.getElementById('id-disp-drag-full');
  if (tmpDiv3) tmpDiv3.remove();

  $('#id-all_maps').append(
    '\
      <div class="row" id="id-disp-drag-double" style="justify-content: space-between; "> \
        <div id="parent-chart-assign-drivers-asis"> \
          <div id="chart-assign-drivers" style="width: 46vw; height: 85vh;"></div> \
        </div> \
        <div id = "parent-chart-assign-drivers-tobe" > \
          <div> \
          <button class="btn btn-success btn-sm" style="padding: 5px 50px" id="id-btn-accept" onclick="accept_schedule()"> \
          Accept </button> \
          <button class="btn btn-danger btn-sm" style="padding: 5px 50px" id="id-btn-reject" onclick="reject_schedule()"> \
          Reject </button> \
          </div> \
          <div id="chart-assign-drivers-tobe" style="width: 46vw; height: 82vh;"></div> \
        </div > \
      </div > \
    '
  );

  build_tour_desc_div((parent_div_id = 'id-disp-drag-double'));
}

function insert_disp_drag_double_1() {
  let tmpDiv = document.getElementById('id-tour-desc-container');
  if (tmpDiv) tmpDiv.remove();

  let tmpDiv2 = document.getElementById('id-disp-drag-double');
  if (tmpDiv2) tmpDiv2.remove();

  let tmpDiv3 = document.getElementById('id-disp-drag-full');
  if (tmpDiv3) tmpDiv3.remove();

  $('#id-all_maps').append(
    '\
      <div class="row" id="id-disp-drag-double" style="justify-content: space-between; "> \
        <div id="parent-chart-assign-drivers-asis"> \
          <div id="chart-assign-drivers" style="width: 44vw; height: 85vh;"></div> \
        </div> \
        <div id = "parent-chart-assign-drivers-tobe" > \
          <div> \
          <button class="btn btn-success btn-sm" style="padding: 5px 50px" id="id-btn-accept" onclick="stop_preview()"> \
          OK </button> \
          </div> \
          <div id="chart-assign-drivers-tobe" style="width: 44vw; height: 82vh;"></div> \
        </div > \
    </div > \
    '
  );

  build_tour_desc_div((parent_div_id = 'id-disp-drag-double'));
}

function insert_disp_drag_full() {
  let tmpDiv = document.getElementById('id-tour-desc-container');
  if (tmpDiv) tmpDiv.remove();

  let tmpDiv2 = document.getElementById('id-disp-drag-double');
  if (tmpDiv2) tmpDiv2.remove();

  let tmpDiv3 = document.getElementById('id-disp-drag-full');
  if (tmpDiv3) tmpDiv3.remove();

  build_schedule_gantt_chart();
}

function clean_up_map() {
  if (!document.getElementById('id-remove-map').checked) {
    return;
  }

  // $('#tours_map').remove();
  // $('#parent-draw-tour').append(
  //   '<div id="tours_map" style="width: 15vw; height: 85vh; vertical-align: top"></div>'
  // );
  // load_map();
}

function disp_filter_tours_div() {
  let x = document.getElementById('id-apply-filters');
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

// function close_search_div() {

//   let x = document.getElementById("id-search-div");
//   if (x.style.display === "none") {
//     x.style.display = "block";
//   } else {
//     x.style.display = "none";
//   }
// };

function disp_loc_win_div() {
  let x = document.getElementById('id-insert-location-frame');
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_driver_win_div() {
  clean_up_driver_info_portal();
  document.getElementById('id-current-ctrlby').innerText = '';
  selectElement((id = 'id-ctrl-by-loc-driversetup'), (valueToSelect = ''));

  // document.getElementById('id-current-operator').innerText = 'FedEx Express'
  selectElement(
    (id = 'id-operator-driversetup'),
    (valueToSelect = 'FedEx Express')
  );

  document.getElementById('id-current-start-loc').innerText = '';
  selectElement((id = 'id-start-loc-code-driversetup'), (valueToSelect = ''));

  document.getElementById('id-drivername-driversetup').value = '';
  document.getElementById('id-drivername-driversetup').disabled = false;

  let x = document.getElementById('id-insert-driver-frame');
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_runtime_win_div() {
  let x = document.getElementById('id-manage-runtimes');
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_opt_win_div() {
  let x = document.getElementById('id-manage-optimization');
  if (x.style.display === 'none') {
    x.style.display = 'block';
    populate_user_settings();
  } else {
    x.style.display = 'none';
  }
}

function disp_note_win_div() {
  let x = document.getElementById('id-note-to-driver-parent');
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

// function disp_toolbox_win_div() {

//   let x = document.getElementById("id-toolbox-div");
//   let y = document.getElementById('id-toolbox-header-div');

//   if (x.style.display === "none") {
//     x.style.display = "block";
//     y.style.marginBottom = 0
//   } else {
//     x.style.display = "none";
//     y.style.marginBottom = '-1%'
//   }
// };

function disp_toolbox_winII_div() {
  let x = document.getElementById('id-toolboxII');
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_days_to_apply() {
  let x = document.getElementById('id-days-to-apply-master-plan');

  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_save_shift_data_win() {
  let x = document.getElementById('id-save-shift-data');

  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

// function close_time_tooltip() {

//   let x = document.getElementById("dragstatus");

//   if (!(document.getElementById('id-chg-time-on-drop').checked)) {
//     x.style.display = "none";
//   }

// };

function close_time_dragstatus() {
  let x = document.getElementById('dragstatus');
  x.style.display = 'none';
}

function close_tooltip_lbl() {
  let x = document.getElementById('id-tooltip-info');
  x.style.display = 'none';
}

function disp_mov_modify_movement_details() {
  let x = document.getElementById('id-modify-traffic-type');
  document.getElementById('id-mov-loc-string-modify').value =
    document.getElementById('id-right-clicked-movement-lhid').value;

  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_search_win_div() {
  let x = document.getElementById('id-search-windows');

  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function disp_mov_win_div(keep_open = false) {
  let x = document.getElementById('id-insert-movement-frame');
  let pipe_seperated_inserted_movs_string = '';

  document.getElementById('id-movement-loc-string').innerText = '';

  if (keep_open) {
    // document.getElementById("id-toolbox-div").style.display = 'block';
    x.style.display = 'block';
    return;
  }

  if (x.style.display === 'none') {
    // document.getElementById("id-toolbox-div").style.display = 'block';
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }

  document.getElementById('id-add-hoc-move-dep-time').disabled = false;
  document.getElementById('id-loc-lookup-list').disabled = false;
  document.getElementById('id-movement-loc-string').disabled = false;
}

function open_route_application() {
  if (
    document.getElementById('id-route-application-path').style.display == 'none'
  ) {
    document.getElementById('id-route-application-path').style.display =
      'block';
  } else {
    document.getElementById('id-route-application-path').style.display = 'none';
  }

  // window.open("http://emaps.prod.fedex.com/egis/app/route/");
}

function vacuum() {
  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  set_title('VACUUM is running ...');
  $.post(
    (url = `${apiBaseURI}/vacuum`),
    (data = {}),
    (success = function (response) {
      set_default_title();
      create_popup((title = 'INFO'), (message = response.message));
    })
  );
}

function backup_db() {
  set_title('Backup is running ...');
  py2js((str_func_name = 'backup_db'), (dct_params = {}), (url = '/drivers'));
  set_default_title();
}

function export_local_schedule() {
  set_title('Exporting schedule ...');

  let status = py2js(
    (str_func_name = ''),
    (dct_params = {}),
    (url = '/save-final-vsn-schedule')
  );

  create_popup((title = 'Exporting schedule'), (message = status.message));
  set_default_title();
  get_chart_data();
}

async function import_selected_schedule() {
  let scn_name = $('#id-master-plan-dropdown').val();

  let status = py2js(
    (str_func_name = ''),
    (dct_params = { scn_name: scn_name }),
    (url = '/load-selected-schedule')
  );

  if (status.code === 200) {
    let is_pwd_valid = true;
    // if (status.pwd_required) {
    //   is_pwd_valid = await showSwalInput('Please Enter password');
    // }

    if (is_pwd_valid) {
      window.location.href = '/';
    }
  } else {
    create_popup((title = 'Importing delta data'), (message = status.error));
    set_default_title();
  }
}

function import_delta_data() {
  let status_delta_import = sync_post('/import-delta-data');
  if (status_delta_import.code === 200) {
    window.location.href = '/';
  } else {
    create_popup(
      (title = 'Importing delta data'),
      (message = status_delta_import.message)
    );
    set_default_title();
  }
}

function set_language(lang = 'en') {
  let status = sync_post('/set-language', { lang: lang });
  create_popup((title = 'Setting language'), (message = status.message));
}

function fresh_start() {
  set_title('Clearing cached schedule ...');
  let status = sync_post('/fresh-start');

  if (status.code === 400) {
    create_popup(
      (title = 'Clearing cached schedule'),
      (message = status.message)
    );
  }

  set_default_title();
}

function refresh_shift_index() {
  set_title('Refreshing shift index ...');
  py2js(
    (str_func_name = 'refresh_shift_index'),
    (dct_params = {
      page_num: window.currPage,
    }),
    (url = '/drivers')
  );

  set_default_title();
}

function review_shifts(refresh_all = false) {
  if (refresh_all === true) {
    set_title('Refreshing Tours ...');
    let dct_chart_data_rebuild_tours = py2js(
      (str_func_name = 'review_shifts'),
      (dct_params = {
        refresh_all: true,
      }),
      (url = '/drivers')
    );

    create_popup(
      (title = 'INFO'),
      (message = dct_chart_data_rebuild_tours.message)
    );

    set_default_title();
    return;
  }
}

function propose_shifts(right_clicked = false) {
  set_title('Exploring tours to assign movements ...');
  let status = py2js(
    (str_func_name = 'review_shifts'),
    (dct_params = {
      search4shift: true,
      set_right_click_id: right_clicked,
    }),
    (url = '/drivers')
  );

  create_popup((title = 'INFO'), (message = status.message));
  set_default_title();
}

// %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function hide_progress_bar() {
  let div_progressbar = document.getElementById('id-progressbar');
  if (div_progressbar.style.display == 'none') {
    div_progressbar.style.display = 'block';
    document.getElementById('id-progress-bar-hidden').style.display = 'none';
  } else {
    div_progressbar.style.display = 'none';
    document.getElementById('id-progress-bar-hidden').style.display = 'block';
  }
}

function display_doc() {
  window.open('/display-schedule-docs', '_blank');
}

// function disp_locs() {
//   window.open('/display-locations-on-map', '_blank');
// }

function get_driver_note(driver) {
  let __dct_driver_note = py2js(
    (str_func_name = 'get_driver_note'),
    (dct_params = { driver: driver }),
    (url = '/drivers')
  );

  return __dct_driver_note.message;
}

function ask_gpt() {
  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  $.post(
    (url = `${apiBaseURI}/ask_gpt`),
    (data = {}),
    (success = function (response) {
      if (response.code === 400) {
        create_popup((title = 'INFO'), (message = response.message));
        return;
      }
    })
  );
}

function modify_movement_details() {
  let _tu = document.getElementById('id-mov-tu-dest-modify').value;
  let __ttype = document.getElementById('id-mov-traffic-type-modify').value;
  let __loc_strng = document.getElementById('id-mov-loc-string-modify').value;
  let __dep_day = document.getElementById('id-modify-mov-dep-day').value;
  let __vehicle = document.getElementById('id-mov-vehicle-type-modify').value;

  hidePopup((id = 'id-modify-traffic-type'));

  if (__loc_strng == '') {
    create_popup(
      (title = 'Loc string is Blank'),
      (message = 'Invalid loc string! Example: ADX.DZ5.1230')
    );
    return;
  }

  let chart_data = py2js(
    (str_func_name = 'modify_movement_details'),
    (dct_params = {
      page_num: window.currPage,
      traffic_type: __ttype,
      loc_string: __loc_strng,
      vehicle: __vehicle,
      depday: __dep_day,
      tu_dest: _tu,
      movementid: Number(
        document.getElementById('id-right-clicked-movement-id').value
      ),
    }),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(chart_data)) {
    load_driver_shift_chart(
      (dct_chart_data = chart_data),
      (render_to = 'chart-assign-drivers')
    );
  }
}

function blank_shift() {
  let __tour_from = document.getElementById('id-tour-loc-from').value;

  let dct_chart_data_with_blank_shift = py2js(
    (str_func_name = 'blank_shift'),
    (dct_params = {
      page_num: window.currPage,
      loc: __tour_from,
    }),
    (url = '/drivers')
  );

  load_driver_shift_chart(
    (dct_chart_data = dct_chart_data_with_blank_shift),
    (render_to = 'chart-assign-drivers')
  );
}

function run_diagnostics() {
  set_title('Running diagnostics ...');
  let status = py2js(
    (str_func_name = 'run_diagnostics'),
    (dct_params = {}),
    (url = '/drivers')
  );

  create_popup((title = 'INFO'), (message = status.message));

  set_default_title();
}

function open_user_manual() {
  window.open('/docs/', '_blank');
}

function open_technical_docs() {
  window.open('/tdocs/', '_blank');
}

function preview_log_file() {
  window.open('/status_page', '_blank');
}

function reboot() {
  $.get(
    (url = '/reboot-lion'),
    (data = {}),
    (success = function (response) {
      if (response.code == 400) {
        if (response.message != '') {
          create_popup(
            (title = 'Rebooting'),
            (message = response.message),
            (icon = 'info')
          );
        }
      }
    })
  );
}


function extract_locations_info() {
  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  set_title('Extracting locations ...');
  $.post(
    (url = `${apiBaseURI}/extract-locations`),
    (data = {}),
    (success = function (response) {
      create_popup((title = 'INFO'), (message = response.message));
    })
  );

  set_default_title();
}

function cache_optimization_params() {
  let drivingtimeb4break = $('#id-drivingtimeb4break').val();
  let minbreaktimeworking = $('#id-minbreaktimeworking').val();
  let workingtimeb4break = $('#id-workingtimeb4break').val();
  let minbreaktime = $('#id-minbreaktime').val();
  let maxreposdrivmin = $('#id-maxreposdrivmin').val();
  let maxcontime = $('#id-maxcontime').val();
  let maxtourdur = $('#id-maxtourdur').val();
  let maxdrivingdur = $('#id-maxdrivingdur').val();
  let excluded_locs = $('#id-loc-code-with-no-driver').val();
  let dblman_shift_dur = $('#id-dblman-shift-dur').val();
  let empty_downtime = $('#id-empty-mov-downtime').val();
  let maxdowntime_maxreposmin = $('#id-maxdowntime-maxrepostime-II').val();
  let vehicle_code = $('#id-vehicle-type-optimization').val();
  let mip_solver = $('#id-select-mip-solver').val();

  let dctms = sync_post('/cache-opt-params', {
    apply_max_drivers_per_loc: document.getElementById(
      'id-apply-max-resource-per-loc'
    ).checked,
    drivingtimeb4break: Number(drivingtimeb4break),
    workingtimeb4break: Number(workingtimeb4break),
    minbreaktime: Number(minbreaktime),
    minbreaktimeworking: Number(minbreaktimeworking),
    maxreposdrivmin: Number(maxreposdrivmin),
    maxcontime: Number(maxcontime),
    maxtourdur: Number(maxtourdur),
    maxdrivingdur: Number(maxdrivingdur),
    excluded_locs: excluded_locs,
    dblman_shift_dur: dblman_shift_dur,
    empty_downtime: empty_downtime,
    maxdowntime_maxreposmin: maxdowntime_maxreposmin,
    mip_solver: mip_solver,
    vehicle_code: vehicle_code,
  });

  return dctms.Message;
}

function set_dropdown_option(html_element_id, List_of_values = []) {
  let _dropdown_object = document.getElementById(html_element_id);
  if (_dropdown_object === undefined || _dropdown_object === null) {
    return;
  }

  if (List_of_values.length > 0) {
    for (let i = 0; i < _dropdown_object.options.length; i++) {
      _dropdown_object.options[i].selected =
        List_of_values.indexOf(_dropdown_object.options[i].value) >= 0;
    }

    // move selected options to the top, keep this:
    $('#' + html_element_id + ' option:selected').prependTo(
      '#' + html_element_id
    );
  }
  $('#' + html_element_id).selectpicker('refresh');
}

function set_switch_value(html_element_id, value) {
  let state = document.getElementById(html_element_id).checked;
  if (!(Number(state) == Number(value))) {
    document.getElementById(html_element_id).click();
  }
}

function populate_user_settings() {
  let _dct_params = py2js(
    (str_func_name = 'populate_user_settings'),
    (dct_params = {}),
    (url = '/drivers')
  );

  if (_dct_params && !$.isEmptyObject(_dct_params)) {
    let dct_vals = _dct_params.dct_vals;
    let dct_elements = _dct_params.dct_elements;

    for (let elem in dct_elements) {
      if (dct_elements[elem].length > 0) {
        let elem_id = `${dct_elements[elem]}`;
        if (elem_id.length > 3) {
          if (elem_id.includes('dropdown')) {
            let lst_vals = dct_vals[elem].split(',').map((item) => item.trim());
            set_dropdown_option(
              (html_element_id = elem_id),
              (List_of_values = lst_vals)
            );
          } else if (elem_id.includes('switch')) {
            set_switch_value(
              (html_element_id = elem_id),
              (value = dct_vals[elem])
            );
          } else {
            document.getElementById(elem_id).value = dct_vals[elem];
          }
        }
      }
    }
    return;
  }
}

function export_schedule_as(is_master_plan = false) {
  let scn_name = $('#id-scenario-name').val();
  let pwd = $('#id-scenario-pwd').val();
  let pwd_verify = $('#id-scenario-pwd-verification').val();

  hidePopup((id = 'id-save-shift-data'));

  if (pwd != '') {
    if (pwd.length < 6) {
      create_popup(
        (title = 'Too short pwd'),
        (message = 'Password is too short! Minimum length is 6 characters.'),
        (icon = 'info')
      );
      return;
    }

    if (!(pwd_verify === pwd)) {
      create_popup(
        (title = 'Password mismatch'),
        (message = 'Password could not be verified!'),
        (icon = 'info')
      );
      return;
    }
  }

  let scn_note = document.getElementById('id-scenario-note').innerText;

  if (scn_name != '') {
    set_title('Saving schedule as ' + scn_name);
  } else {
    set_title('Saving schedule ...');
  }

  let _status = py2js(
    (str_func_name = ''),
    (dct_params = {
      page_num: window.currPage,
      scn_name: scn_name,
      pwd: pwd,
      scn_note: scn_note,
      is_master_plan: is_master_plan,
    }),
    (url = '/save-final-vsn-schedule'),
    (async = false)
  );

  console.log(_status);
  set_default_title();
  create_popup((title = 'Exporting schedule'), (message = _status.message));
  get_chart_data();
}

function fb2lion() {
  let sts = py2js(
    (str_func_name = 'fb2lion'),
    (dct_params = {}),
    (url = '/drivers')
  );
}

function set_right_click_id(point_id) {
  py2js(
    (str_func_name = 'set_right_click_id'),
    (dct_params = { point_id: point_id }),
    (url = '/drivers')
  );
}

function sort_by_tourLocString() {
  let dctmsg = py2js(
    (str_func_name = 'enable_tour_locstring_sort'),
    (dct_params = {}),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(dctmsg)) {
    create_popup(
      (title = 'Loading chart failed'),
      (message = dctmsg.messag),
      (icon = 'info')
    );

    return;
  }

  window.location.href = '/loading_schedule/';

}

function is_basket_empty() {
  return py2js(
    (str_func_name = 'is_basket_empty'),
    (dct_params = {}),
    (url = '/drivers')
  );
}

function add_shifts_to_my_basket(get_right_click_id = false) {
  let __dct_drivers = py2js(
    (str_func_name = 'add_shifts_to_my_basket'),
    (dct_params = {
      get_right_click_id: get_right_click_id,
      drivers: window.selected_tours_to_take_action,
      page_num: window.currPage,
    }),
    (url = '/drivers')
  );

  window.selected_tours_to_take_action = [];

  document.getElementById('id-basket-btn').innerHTML =
    '<i class="tim-icons icon-cart"></i> My Basket' +
    ' (' +
    __dct_drivers.drivers.length +
    ')';
}

function remove_shifts_from_my_basket(get_right_click_id = false) {
  let __dct_drivers = py2js(
    (str_func_name = 'remove_shifts_from_my_basket'),
    (dct_params = {
      drivers: window.selected_tours_to_take_action,
      page_num: window.currPage,
      get_right_click_id: get_right_click_id,
    }),
    (url = '/drivers')
  );

  window.selected_tours_to_take_action = [];

  document.getElementById('id-basket-btn').innerHTML =
    '<i class="tim-icons icon-cart"></i> My Basket' +
    ' (' +
    __dct_drivers.drivers.length +
    ')';

  load_my_basket_data();
}

function barwith_enlarge() {
  let __dct_barwith_enlarge = py2js(
    (str_func_name = 'barwith_enlarge'),
    (dct_params = { page_num: window.currPage }),
    (url = '/drivers')
  );

  load_driver_shift_chart(
    (dct_chart_data = __dct_barwith_enlarge),
    (render_to = 'chart-assign-drivers')
  );
}

function barwith_shrink() {
  let __dct_barwith_shrink = py2js(
    (str_func_name = 'barwith_shrink'),
    (dct_params = { page_num: window.currPage }),
    (url = '/drivers')
  );

  load_driver_shift_chart(
    (dct_chart_data = __dct_barwith_shrink),
    (render_to = 'chart-assign-drivers')
  );
}

function empty_basket() {
  let clear_bskt_status = sync_post('/empty-basket', (dct_params = {}));

  if (clear_bskt_status.code === 400) {
    create_popup(
      (title = 'Emptying basket failed'),
      (message = clear_bskt_status.error),
      (icon = 'info')
    );
    return;
  }

  window.selected_tours_to_take_action = [];

  document.getElementById('id-basket-btn').innerHTML =
    '<i class="tim-icons icon-cart"></i> My Basket' +
    ' (' +
    clear_bskt_status.drivers.length +
    ')';
}

function selectElement(id, valueToSelect) {
  let lst_values_2_select = [];
  lst_values_2_select.push(String(valueToSelect));
  set_dropdown_option(
    (html_element_id = id),
    (List_of_values = lst_values_2_select)
  );

  // let element = document.getElementById(id);
  // element.value = valueToSelect;
}

function setDragStatus(status) {
  let x = (document.getElementById('dragstatus').style.display = 'block');
  document.getElementById('dragstatus').innerText = status;
  document.getElementById('dragstatus').style.backgroundColor = 'lightgray';
}

function toggle_labels() {
  load_driver_shift_chart((dct_chart_data = dct_chart_data_latest));
}

function reset_chart() {
  load_driver_shift_chart((dct_chart_data = dct_chart_data_latest));
  clear_selected_tours_to_take_action();
  draw_tour();
}

function set_axis_ranges_out(d) {
  let chart_data = py2js(
    (str_func_name = 'set_axis_ranges'),
    (dct_params = {
      page_num: window.currPage,
      zoom: 'out',
      hours: 2,
    }),
    (url = '/drivers')
  );
  load_driver_shift_chart((dct_chart_data = chart_data));
}

function set_axis_ranges_in(d) {
  let chart_data2 = py2js(
    (str_func_name = 'set_axis_ranges'),
    (dct_params = {
      page_num: window.currPage,
      zoom: 'in',
      hours: 2,
    }),
    (url = '/drivers')
  );
  load_driver_shift_chart((dct_chart_data = chart_data2));
}

function get_driver_info(d = '', get_right_click_id = false) {
  let dct_driver_info_out = py2js(
    (str_func_name = 'get_driver_info'),
    (dct_params = { driver: d, get_right_click_id: get_right_click_id }),
    (url = '/drivers')
  );

  let dct_driver_info = dct_driver_info_out.data;
  let __msg = dct_driver_info_out.message;
  let __selected_days = dct_driver_info_out.weekdays;

  if ($.isEmptyObject(dct_driver_info)) {
    return;
  }

  document.getElementById('id-drivername-driversetup').value =
    dct_driver_info['shiftname'];
  document.getElementById('id-rename-shift-to').value =
    dct_driver_info['shiftname'];
  document.getElementById('id-drivername-driversetup').disabled = true;

  if (!$.isEmptyObject(dct_driver_info)) {
    document.getElementById('id-current-ctrlby').innerText =
      dct_driver_info['controlled by'];
    selectElement(
      (id = 'id-ctrl-by-loc-driversetup'),
      (valueToSelect = dct_driver_info['controlled by'])
    );

    document.getElementById('id-current-operator').innerText =
      dct_driver_info['operator'];
    selectElement(
      (id = 'id-operator-driversetup'),
      (valueToSelect = dct_driver_info['operator'])
    );

    document.getElementById('id-current-start-loc').innerText =
      dct_driver_info['start position'];
    selectElement(
      (id = 'id-start-loc-code-driversetup'),
      (valueToSelect = dct_driver_info['start position'])
    );

    if (dct_driver_info['double_man'] == true) {
      document.getElementById('id-shift-double-man-lbl').innerText =
        'Double man';
    }

    selectElement(
      (id = 'id-shift-vehicle-type'),
      (valueToSelect = dct_driver_info['vehicle'])
    );

    if (dct_driver_info['vehicle'] == '1') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Tractor-trailer 2/3 Axles 80m3';
    } else if (dct_driver_info['vehicle'] == '2') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Truck 12 ton';
    } else if (dct_driver_info['vehicle'] == '3') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Truck 7.5 ton';
    } else if (dct_driver_info['vehicle'] == '4') {
      document.getElementById('id-shift-vehicle-lbl').innerText = 'Van';
    } else if (dct_driver_info['vehicle'] == '7') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Truck 18 Ton';
    } else if (dct_driver_info['vehicle'] == '6') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        '18 Ton + Drop-body';
    } else if (dct_driver_info['vehicle'] == '5') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Unit + Swap body';
    } else if (dct_driver_info['vehicle'] == '10') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Unit + Long D/D Trailer';
    } else if (dct_driver_info['vehicle'] == '9') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Unit + Long Trailer';
    } else if (dct_driver_info['vehicle'] == '8') {
      document.getElementById('id-shift-vehicle-lbl').innerText =
        'Unit + D/D Trailer';
    }

    if (dct_driver_info['double_man'] == true) {
      if (!document.getElementById('id-double-man-shift').checked) {
        document.getElementById('id-double-man-shift').click();
      }
    }

    if (dct_driver_info['double_man'] == false) {
      if (document.getElementById('id-double-man-shift').checked) {
        document.getElementById('id-double-man-shift').click();
      }
    }

    if (dct_driver_info['hbr'] == false) {
      if (document.getElementById('id-hbr-rule-applied').checked) {
        document.getElementById('id-hbr-rule-applied').click();
      }
    }

    if (dct_driver_info['hbr'] == true) {
      if (!document.getElementById('id-hbr-rule-applied').checked) {
        document.getElementById('id-hbr-rule-applied').click();
      }
    }

    if (dct_driver_info.source == 'ROCS') {
      document.getElementById('id-driver-info-message-lbl').innerText =
        'WARNNING: The data is coming from ROCS. Please update the details!';
      // create_popup(title = 'ROCS data', message = 'The data is coming from ROCS. Please update the details!');
    }
  }

  if (__selected_days.length > 0) {
    document.getElementById('id-lbl-shift-running-weekday').innerText =
      __selected_days.join('; ');

    let __running_days_dropdown = document.getElementById(
      'id-shift-running-weekday'
    );
    __running_days_dropdown.selectedIndex = -1;

    if (__selected_days.length > 0) {
      for (let j = 0; j < __running_days_dropdown.options.length; j++) {
        if (
          __selected_days.indexOf(__running_days_dropdown.options[j].value) >= 0
        ) {
          __running_days_dropdown.options[j].selected = true;
        }
      }
      $('#id-shift-running-weekday option:selected').prependTo(
        '#id-shift-running-weekday'
      );
    }
  }

  if (__msg != '') {
    document.getElementById('id-driver-info-message-lbl').innerText = __msg;
  }
}

function clean_up_driver_info_portal() {
  document.getElementById('id-drivername-driversetup').value = '';
  document.getElementById('id-rename-shift-to').value = '';
  document.getElementById('id-drivername-driversetup').disabled = true;

  document.getElementById('id-current-ctrlby').innerText = '';
  selectElement((id = 'id-ctrl-by-loc-driversetup'), (valueToSelect = ''));

  document.getElementById('id-current-operator').innerText = '';
  selectElement(
    (id = 'id-operator-driversetup'),
    (valueToSelect = 'FedEx Express')
  );

  document.getElementById('id-current-start-loc').innerText = '';
  selectElement((id = 'id-start-loc-code-driversetup'), (valueToSelect = ''));

  document.getElementById('id-shift-double-man-lbl').innerText = '';

  selectElement((id = 'id-shift-vehicle-type'), (valueToSelect = ''));
  document.getElementById('id-shift-vehicle-lbl').innerText = '';

  if (document.getElementById('id-double-man-shift').checked) {
    document.getElementById('id-double-man-shift').click();
  }

  if (!document.getElementById('id-hbr-rule-applied').checked) {
    document.getElementById('id-hbr-rule-applied').click();
  }

  document.getElementById('id-driver-info-message-lbl').innerText = '';

  document.getElementById('id-lbl-shift-running-weekday').innerText = '';

  let wkdays = document.getElementById('id-shift-running-weekday').options;

  for (let i = 0; i < wkdays.length; i++) {
    wkdays[i].selected = false;
  }
  $('#id-shift-running-weekday').selectpicker('refresh');
}

function save_note() {
  let __driver = $('#id-driver-to-add-note').val();
  const par = document.getElementById('id-driver-note');
  let my_note = par.textContent;

  let _chart_data = py2js(
    (str_func_name = 'save_shift_note'),
    (dct_params = { shift_note: my_note, driver: __driver }),
    (url = '/drivers')
  );

  disp_note_win_div();

  if (!$.isEmptyObject(_chart_data)) {
    insert_disp_drag_full();
    load_driver_shift_chart((dct_chart_data = _chart_data));
  }
}

function accept_schedule() {
  let status_accept_schedule = py2js(
    (str_func_name = 'accept_schedule'),
    (dct_params = { page_num: window.currPage }),
    (url = '/drivers')
  );

  insert_disp_drag_full();
  load_driver_shift_chart((dct_chart_data = status_accept_schedule));
  // clean_up_map()
}

function reject_schedule() {
  let status_reject_schedule = py2js(
    (str_func_name = 'reject_schedule'),
    (dct_params = { page_num: window.currPage }),
    (url = '/drivers')
  );

  insert_disp_drag_full();
  load_driver_shift_chart((dct_chart_data = status_reject_schedule));
}

function refresh_current_page_on_drop() {
  let dct_adjusted_chart_data = py2js(
    (str_func_name = 'refresh_current_page_on_drop'),
    refresh_current_page_on_drop(
      (dct_params = {
        page_num: window.currPage,
        dct_event_newPoint: e.newPoint,
        point_id: Number(this.id),
        current_driver: this.driver,
        try_all: document.getElementById('id-try-all-drivers-on-page').checked,
      })
    ),
    (url = '/drivers')
  );

  if ('current' in dct_adjusted_chart_data) {
    insert_disp_drag_double();
    load_driver_shift_chart(
      (dct_chart_data = dct_adjusted_chart_data.current),
      (render_to = 'chart-assign-drivers')
    );
    load_driver_shift_chart(
      (dct_chart_data = dct_adjusted_chart_data.scn),
      (render_to = 'chart-assign-drivers-tobe')
    );
    return;
  }

  insert_disp_drag_full();
  load_driver_shift_chart(
    (dct_chart_data = dct_adjusted_chart_data),
    (render_to = 'chart-assign-drivers')
  );
}

function delete_if_blank_else_fixUnfix(shift) {
  let _chart_data = py2js(
    (str_func_name = 'delete_if_blank_else_fixUnfix'),
    (dct_params = {
      shift: shift,
      page_num: window.currPage,
    }),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(_chart_data)) {
    load_driver_shift_chart((dct_chart_data = _chart_data));
  }
}

function toggle_shift_fix_unfix(shift) {
  let _chart_data = py2js(
    (str_func_name = 'delete_if_blank_else_fixUnfix'),
    (dct_params = {
      shift: shift,
      page_num: window.currPage,
    }),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(_chart_data)) {
    load_driver_shift_chart((dct_chart_data = _chart_data));
  }
}

async function update_fixed_tours() {
  let update_fixed_tours_status = py2js(
    (str_func_name = 'update_fixed_tours'),
    (dct_params = {
      drivers: window.selected_tours_to_take_action,
      page_num: window.currPage,
    }),
    (url = '/drivers')
  );

  clear_selected_tours_to_take_action();

  let status = await create_popup_async(
    (title = 'Update Fixed Tours'),
    (message = update_fixed_tours_status.update_fixed_tours_message),
    (type = 'Info')
  );

  if (status == 'OK') {
    if (!$.isEmptyObject(update_fixed_tours_status.chart_data)) {
      load_driver_shift_chart(
        (dct_chart_data = update_fixed_tours_status.chart_data)
      );
    }
  }
}

async function unfix_all_drivers() {
  let un_fixed_tours_status = py2js(
    (str_func_name = 'update_fixed_tours'),
    (dct_params = {
      page_num: window.currPage,
      unfix_all: 'Yes',
    }),
    (url = '/drivers')
  );

  let status = await create_popup_async(
    (title = 'Update Fixed Tours'),
    (message = un_fixed_tours_status.update_fixed_tours_message),
    (type = 'Info')
  );

  if (status == 'OK') {
    if (!$.isEmptyObject(un_fixed_tours_status.chart_data)) {
      load_driver_shift_chart(
        (dct_chart_data = un_fixed_tours_status.chart_data)
      );
    }
  }
}

function add_a_traffic_type() {
  let status = py2js(
    (str_func_name = 'add_a_traffic_type'),
    (dct_params = {}),
    (url = '/drivers')
  );

  create_popup((title = 'Add a vehicle'), (message = status.message));
}

function add_a_vehicle() {
  let status = py2js(
    (str_func_name = 'add_a_vehicle'),
    (dct_params = {}),
    (url = '/drivers')
  );

  create_popup((title = 'Add a vehicle'), (message = status.message));
}

function extract_movements_to_process(extract_all = false) {
  set_title('Extracting movements info ...');

  let vehicle = 0;
  if (extract_all === false) {
    vehicle = Number($('#id-vehicle-type-optimization').val());
  }

  py2js(
    (str_func_name = 'extract_movements_to_process'),
    (dct_params = {
      page_num: window.currPage,
      vehicle_code: vehicle,
      extract_all: extract_all, //document.getElementById('id-excl-fixed-movements').checked,
      days: [],
    }),
    (url = '/drivers')
  );

  set_default_title();
}

async function fix_all_drivers() {
  let fixed_tours_status = py2js(
    (str_func_name = 'update_fixed_tours'),
    (dct_params = {
      page_num: window.currPage,
      fix_all: 'Yes',
    }),
    (url = '/drivers')
  );

  let status = await create_popup_async(
    (title = 'Update Fixed Tours'),
    (message = fixed_tours_status.update_fixed_tours_message),
    (type = 'Info')
  );

  if (status == 'OK') {
    if (!$.isEmptyObject(fixed_tours_status.chart_data)) {
      load_driver_shift_chart((dct_chart_data = fixed_tours_status.chart_data));
    }
  }
}

function round_time_to_nearest_5min() {
  let coeff = 1000 * 60 * 5;
  const rounded = new Date(Math.round(timestamp / coeff) * coeff);
  const result = rounded.toISOString().slice(0, 16);
  return result;
}

function toggle_logging() {
  const log_enabled = document.getElementById(
    'id-enable-logging-switch'
  ).checked;
  sync_post('/toggle-logging', { log_enabled: log_enabled });
}

function set_user_param(par, html_element_id) {
  set_title('Setting user params ...');
  let obj_val = undefined;
  if (html_element_id.includes('switch')) {
    obj_val = document.getElementById(html_element_id).checked;
  } else if (html_element_id.includes('dropdown')) {
    let _dropdown = document.getElementById(html_element_id);
    obj_val = _dropdown.options[_dropdown.selectedIndex].value;
  } else {
    obj_val = document.getElementById(html_element_id).value;
  }

  py2js(
    (str_func_name = 'set_user_param'),
    (dct_params = {
      param: par,
      val: obj_val,
    }),
    (url = '/drivers')
  );

  set_default_title();

  if (par == 'enable_zoom') {
    get_chart_data();
  }
}

function set_egis_scenario() {
  set_title('Setting egis scn ...');

  let _cdata = py2js(
    (str_func_name = 'set_egis_scenario'),
    (dct_params = {
      runtimes_scenario: document.getElementById('id-egis-scenarios-dropdown')
        .value,
    }),
    (url = '/drivers')
  );

  set_default_title();

  load_driver_shift_chart((dct_chart_data = _cdata.chart_data));
  if (_cdata.message != '') {
    create_popup((title = 'Relaod plan'), (message = _cdata.message));
  }
}

function un_hide_infeas() {
  let status_un_hide_infeas = py2js(
    (str_func_name = 'un_hide_infeas'),
    (dct_params = {
      page_num: window.currPage,
      hide: document.getElementById('id-hide-feas').checked,
    }),
    (url = '/drivers')
  );
  load_driver_shift_chart((dct_chart_data = status_un_hide_infeas));
}

function copy_weekly_optimized_shifts() {
  let wkdays = $('#id-wkdays-to-copy-schedule').val();
  let vehicle_code = $('#id-vehicle-type-optimization').val();

  set_title('Copying schedule ...');
  py2js(
    (str_func_name = 'copy_weekly_optimized_shifts'),
    (dct_params = {
      copy_to_days: wkdays,
      vehicle_code: vehicle_code,
      user_loaded_movs: document.getElementById('id-user-loaded-movements')
        .checked,
      copy_complete_only: document.getElementById(
        'id-copy-complete-shifts-only'
      ).checked,
    }),
    (url = '/drivers')
  );
  set_default_title();
}

function un_hide_fixed() {
  let status_un_hide_fixed = py2js(
    (str_func_name = 'un_hide_fixed'),
    (dct_params = {
      page_num: window.currPage,
      hide: document.getElementById('id-hide-fixed').checked,
    }),
    (url = '/drivers')
  );
  load_driver_shift_chart((dct_chart_data = status_un_hide_fixed));
}

function toggle_search_current_page() {
  py2js(
    (str_func_name = 'toggle_search_current_page'),
    (dct_params = {
      page_num: window.currPage,
      search_curr_page: document.getElementById('id-search-current-page-only')
        .checked,
    }),
    (url = '/drivers')
  );
}

function un_hide_blank() {
  let status_un_hide_blnk = py2js(
    (str_func_name = 'un_hide_blank'),
    (dct_params = {
      page_num: window.currPage,
      hide: document.getElementById('id-hide-blank').checked,
    }),
    (url = '/drivers')
  );
  load_driver_shift_chart((dct_chart_data = status_un_hide_blnk));
}

function undo() {
  let status_undo = py2js(
    (str_func_name = 'undo'),
    (dct_params = {}),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(status_undo)) {
    load_driver_shift_chart((dct_chart_data = status_undo));
  }
}

function delete_changeovers() {
  let __coList = $('#id-changeovers').val();

  if (__coList.length == 0) {
    create_popup(
      (title = 'Deletion failed'),
      (message = 'No changeover was selected!')
    );
    return;
  }

  let status_delete_changeover = py2js(
    (str_func_name = 'delete_changeovers'),
    (dct_params = { changeovers: __coList }),
    (url = '/drivers')
  );

  create_popup(
    (title = 'Deletion failed'),
    (message = status_delete_changeover.message)
  );
}

function generate_kpi_report() {
  set_title('Generating KPI report ...');
  let status = py2js(
    (str_func_name = 'generate_kpi_report'),
    (dct_params = {}),
    (url = '/drivers')
  );

  set_default_title();
  create_popup(
    (title = 'KPI report generation failed'),
    (message = status.message)
  );
}

function un_close_location() {
  handle_location(true);
}

function set_number_of_drivers_per_page() {
  let page_size = Number(
    document.getElementById('id-page-size-dropdown').value
  );
  let status_pgsize = py2js(
    (str_func_name = 'set_number_of_drivers_per_page'),
    (dct_params = {
      page_size: page_size,
    }),
    (url = '/drivers')
  );

  build_schedule_gantt_chart((page_size = page_size));
  load_driver_shift_chart((dct_chart_data = status_pgsize));
  load_chart_on_full_page_load();
}

async function remove_shift_rightclick() {
  let status = await create_popup_with_decision(
    (title = 'Delete Shift'),
    (message = 'Are you sure you wish to delete this shift?'),
    (type = 'warning'), // other options are "success", "error", "warning", "info" or "question"
    (confirmButtonText = 'Delete'),
    (cancelButtonText = 'Cancel')
  );

  if (status === 'Cancelled') {
    set_default_title();
    return;
  }

  let dct_del_shft = py2js(
    (str_func_name = 'remove_shift'),
    (dct_params = {
      pagenum: window.currPage,
    }),
    (url = '/drivers'),
    (async = false)
  );

  if (!$.isEmptyObject(dct_del_shft)) {
    load_driver_shift_chart(
      (dct_chart_data = dct_del_shft),
      (render_to = 'chart-assign-drivers')
    );
  }

  set_default_title();
}

async function remove_shift(shiftname = '') {
  if (shiftname == '') {
    shiftname = $('#id-drivername-driversetup').val();
  }

  hidePopup((id = 'id-insert-driver-frame'));

  if (shiftname == '') {
    create_popup(
      (title = 'Error'),
      (message = 'Specify a shiftname to delete.')
    );
  }

  let status = await create_popup_with_decision(
    (title = 'Delete Shift'),
    (message = 'Are you sure you wish to delete ' + shiftname + '?'),
    (type = 'warning'), // other options are "success", "error", "warning", "info" or "question"
    (confirmButtonText = 'Delete'),
    (cancelButtonText = 'Cancel')
  );

  if (status === 'Cancelled') {
    set_default_title();
    return;
  }

  set_title('Removing ' + shiftname + ' ...');

  let __days = $('#id-shift-running-weekday').val();

  let dct_del_shft = py2js(
    (str_func_name = 'remove_shift'),
    (dct_params = {
      driver_id: shiftname,
      weekdays: __days,
    }),
    (url = '/drivers'),
    (async = false)
  );

  if (!$.isEmptyObject(dct_del_shft)) {
    load_driver_shift_chart(
      (dct_chart_data = dct_del_shft),
      (render_to = 'chart-assign-drivers')
    );
  }

  set_default_title();
}

function handle_drivers_info() {
  set_title('Processing driver info ...');
  hidePopup((id = 'id-insert-driver-frame'));

  let __start = $('#id-start-loc-code-driversetup').val();
  let __sftname = $('#id-drivername-driversetup').val();
  let __sftname2 = $('#id-rename-shift-to').val();
  let __new_supplier = $('#id-new-supplier').val();
  let __supplier = $('#id-operator-driversetup').val();
  let __ctrl_by = $('#id-ctrl-by-loc-driversetup').val();
  let __vehicle_type = $('#id-shift-vehicle-type').val();
  let __dblman = document.getElementById('id-double-man-shift').checked;
  let __hbr_rule = document.getElementById('id-hbr-rule-applied').checked;

  if (__sftname == '') {
    if (__sftname2 == '') {
      create_popup(
        (title = 'Missing shift name'),
        (message = 'Please specify a shift name.')
      );
      return;
    }
  }

  let __days = $('#id-shift-running-weekday').val();

  if (__vehicle_type == undefined || __vehicle_type == '') {
    __vehicle_type = 1;
  }

  if (__days.length == 0) {
    create_popup(
      (title = 'Missing Running days'),
      (message = 'Please specify shift running day(s).')
    );
    return;
  }

  if (__ctrl_by == undefined) {
    __ctrl_by = '';
  }

  if (__start == undefined) {
    __start = '';
  }

  if (__ctrl_by.length == 0 && __start.length > 0) {
    __ctrl_by = __start;
  } else if (__ctrl_by.length > 0 && __start.length == 0) {
    __start = __ctrl_by;
  }

  if (__ctrl_by.length == 0 && __start.length == 0) {
    create_popup(
      (title = 'Missing loc'),
      (message = 'Please specify a start or controling location.')
    );
    return;
  }

  if (__new_supplier.length > 0) {
    __supplier = __new_supplier;
  }

  if (__supplier.length == 0 || __supplier == undefined) {
    __supplier = 'FedEx Express';
  }

  if (__sftname == '') {
    if (__sftname2 != '') {
      __sftname = __sftname2;
    }
  }

  if (!(__sftname.split('.')[0] == __ctrl_by)) {
    __sftname = __ctrl_by + '.' + __sftname;
  }

  if (__sftname2 == '') {
    __sftname2 = __sftname;
  }

  if (__sftname2 != __sftname) {
    if (!(__sftname2.split('.')[0] == __ctrl_by)) {
      __sftname2 = __ctrl_by + '.' + __sftname2;
    }
  }

  // document.getElementById('id-modify-driver-title').innerText = "Add/modify a driver"
  // document.getElementById('id-drivername-driversetup').disabled = false

  let dct_setup_shft = py2js(
    (str_func_name = 'handle_drivers_info'),
    (dct_params = {
      page_num: window.currPage,
      weekdays: __days,
      ctrl_by: __ctrl_by,
      driver_id: __sftname,
      driver_id_2: __sftname2,
      operator: __supplier,
      start_loc: __start,
      double_man: __dblman,
      hbr: __hbr_rule,
      vehicle_type: __vehicle_type,
    }),
    (url = '/drivers'),
    (async = false)
  );

  if (!$.isEmptyObject(dct_setup_shft)) {
    load_driver_shift_chart(
      (dct_chart_data = dct_setup_shft),
      (render_to = 'chart-assign-drivers')
    );
  }

  set_default_title();
}

function update_user_defined_runtimes_mileages() {
  set_title('Updating ...');

  hidePopup('id-manage-runtimes');

  let __runtime = $('#id-drivingtime-runtime-change').val();
  let __miles = $('#id-miles-runtime-change').val();
  let __vehicle = $('#id-selected-travelMode-runtime-change').val();
  let __loc_string = $('#id-loc-strings-to-change-runtimes').val();

  let dct_runtimes4 = py2js(
    (str_func_name = 'update_user_defined_runtimes_mileages'),
    (dct_params = {
      loc_string: __loc_string,
      Vehicle: __vehicle,
      driving_time: __runtime,
      miles: __miles,
      bothDir: document.getElementById('id-chkbox-runtime-change').checked,
    }),
    (url = '/update-user-runtimes')
  );

  hidePopup('id-manage-runtimes');
  if (dct_runtimes4.code === 200) {
    create_popup(
      (title = 'Runtimes update'),
      (message = dct_runtimes4.message)
    );
  } else if (dct_runtimes4.code === 400) {
    create_popup(
      (title = 'Runtimes update'),
      (message = 'Runtimes data was not updated! ' + dct_runtimes4.error)
    );
  }

  set_default_title();
}

function updateRuntimes() {
  var overwrite = document.getElementById(
    'id-chkbox-overwrite-existinglanes-runtimes'
  ).checked;

  let dct = py2js(
    (str_func_name = ''),
    (dct_params = {
      overwrite_existing_lanes: overwrite,
    }),
    (url = '/update-runtimes')
  );

  hidePopup('id-manage-runtimes');
  if (dct.code === 200) {
    create_popup(
      (title = 'Runtimes update'),
      (message = 'Runtimes have been successfully updated!')
    );
  } else if (dct.code === 400) {
    create_popup(
      (title = 'Runtimes update'),
      (message = 'Runtimes data was not updated! ' + dct.error)
    );
  }

  set_default_title();
}

function dumpEmapsData() {
  var __locsFrom = $('#id-loc-code-runtime').val();
  var __locToTypes = $('#id-loc-type-runtimes').val();
  var __locstrings = $('#id-loc-strings').val();

  set_title('Generating eGIS input data ...');

  let dct = py2js(
    (str_func_name = ''),
    (dct_params = {
      LocsFrom: __locsFrom,
      LocToTypes: __locToTypes,
      LocStrings: __locstrings,
    }),
    (url = '/dump-emaps-data')
  );

  hidePopup('id-manage-runtimes');
  if (dct.code === 200) {
    create_popup(
      (title = 'eMaps data dump'),
      (message = 'eMAPS input data has been successfully generated!')
    );
  } else if (dct.code === 400) {
    create_popup(
      (title = 'eMaps data dump'),
      (message = 'eMAPS data was not dumped! ' + dct.error)
    );
  }

  set_default_title();
}

function extract_runtimes() {
  var __locsFrom = $('#id-loc-code-runtime').val();
  var __locToTypes = $('#id-loc-type-runtimes').val();
  var __locstrings = $('#id-loc-strings').val();

  set_title('Extracting runtimes ...');

  let dct = py2js(
    (str_func_name = ''),
    (dct_params = {
      LocsFrom: __locsFrom,
      LocToTypes: __locToTypes,
      LocStrings: __locstrings,
    }),
    (url = '/extract-runtimes-data')
  );

  hidePopup('id-manage-runtimes');
  if (dct.code === 200) {
    create_popup((title = 'Extract runtimes'), (message = dct.message));
  } else if (dct.code === 400) {
    create_popup((title = 'Extract runtimes'), (message = dct.error));
  }

  set_default_title();
}

function minimize_popup(divid, height) {
  var div_obj = document.getElementById(divid);
  let hght = div_obj.style.height;

  if (hght == '10vh') {
    div_obj.style.height = height;
  } else {
    div_obj.style.height = '10vh';
  }
}

function get_egis_coordinates() {
  var postal_code = $('#id-zip-code-manual').val();
  set_title('Extracting coordinates ...');

  let coords = py2js(
    (str_func_name = 'get_egis_coordinates'),
    (dct_params = {
      postal_code: postal_code,
    }),
    (url = '/drivers')
  );

  if (coords.length > 0) {
    document.getElementById('id-lat-lon').value = coords;
    disp_point_on_map();
  }

  set_default_title();
}

function load_location_info() {
  let Loc_to_edit = $('#id-loc-code-locsetup').val();

  let __dct_loc_info = py2js(
    (str_func_name = 'load_location_info'),
    (dct_params = {
      Loc_to_edit: Loc_to_edit,
    }),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(__dct_loc_info)) {
    document.getElementById('id-debrief-time').value =
      __dct_loc_info.dep_debrief_time + ',' + __dct_loc_info.arr_debrief_time;

    document.getElementById('id-lat-lon').value =
      __dct_loc_info.latitude + ',' + __dct_loc_info.longitude;

    document.getElementById('id-turnaround-times').value =
      __dct_loc_info.chgover_driving_min +
      ',' +
      __dct_loc_info.chgover_non_driving_min;

    document.getElementById('id-zip-code-manual').value =
      __dct_loc_info.postcode;
    document.getElementById('id-town-name').value = __dct_loc_info.town;

    document.getElementById('id-loc-code-new').value = __dct_loc_info.loc_code;
    document.getElementById('id-loc-name-new').value =
      __dct_loc_info.location_name;

    selectElement(
      (id = 'id-loc-type-new'),
      (valueToSelect = __dct_loc_info.loc_type)
    );
    selectElement(
      (id = 'id-cust-ctrl-depot'),
      (valueToSelect = __dct_loc_info.ctrl_depot)
    );

    selectElement(
      (id = 'id-live-load-stand-load'),
      (valueToSelect = __dct_loc_info.live_stand_load)
    );

    disp_point_on_map();
  }
}

function handle_location(close_loc = false) {
  set_title('Processing location info ...');

  hidePopup((id = 'id-insert-location-frame'));

  let new_dct_params = {};
  let Loc_to_edit = $('#id-loc-code-locsetup').val();
  let new_loc_code = $('#id-loc-code-new').val();
  let new_loc_name = $('#id-loc-name-new').val();

  let new_loc_type = $('#id-loc-type-new').val();
  let new_loc_coords = $('#id-lat-lon').val();
  let new_loc_town = $('#id-town-name').val();
  let new_loc_turnaround = $('#id-turnaround-times').val();
  let new_loc_debrief = $('#id-debrief-time').val();
  let active_loc = $('#id-active-loc').val();
  let ctrl_depot = $('#id-cust-ctrl-depot').val();
  let live_stand_load = $('#id-live-load-stand-load').val();

  if (
    new_loc_type == 'Customer' &&
    (ctrl_depot == '' || ctrl_depot == undefined)
  ) {
    create_popup(
      (title = 'Controlling depot'),
      (message = 'Please specify a controlling depot!')
    );
    return;
  }

  let zipcode = $('#id-zip-code-manual').val();

  // Show the loc on map
  disp_point_on_map();

  // if ((zipcode == undefined) || (zipcode == '')) {
  //   zipcode = $('#id-zip-code').val()
  // }

  if (zipcode == undefined || zipcode == '') {
    create_popup(
      (title = 'Zipcode is blank'),
      (message = 'Please provide a valid zipcode!')
    );

    return;
  }

  if (new_loc_type == undefined || new_loc_type == '') {
    new_loc_type = 'Customer';
  }

  let dct_setup_loc = py2js(
    (str_func_name = 'handle_location'),
    (dct_params = {
      Loc_to_edit: Loc_to_edit,
      new_loc_code: new_loc_code,
      new_loc_name: new_loc_name,
      new_loc_type: new_loc_type,
      new_loc_coords: new_loc_coords,
      new_loc_town: new_loc_town,
      new_loc_turnaround: new_loc_turnaround,
      zipcode: zipcode,
      new_loc_debrief: new_loc_debrief,
      close_loc: close_loc,
      ctrl_depot: ctrl_depot,
      live_stand_load: live_stand_load,
    }),
    (url = '/drivers')
  );

  set_default_title();
}

function clear_locations_toolbox() {
  document.getElementById('id-zip-code-manual').value = '';
  document.getElementById('id-loc-code-new').value = '';
  document.getElementById('id-loc-name-new').innerText = '';
  document.getElementById('id-lat-lon').innerText = '';
  document.getElementById('id-town-name').innerText = '';

  opts = document.getElementById('id-loc-type-new').options;
  for (var i = 0, opt; (opt = opts[i]); i++) {
    opt.selected = false;
  }
  $('#id-loc-type-new').selectpicker('refresh');

  vhcleopts = document.getElementById('id-cust-ctrl-depot').options;
  for (var i = 0, opt; (opt = vhcleopts[i]); i++) {
    opt.selected = false;
  }
  $('#id-cust-ctrl-depot').selectpicker('refresh');

  locs_opts = document.getElementById('id-loc-code-locsetup').options;
  for (var i = 0, opt; (opt = locs_opts[i]); i++) {
    opt.selected = false;
  }
  $('#id-loc-code-locsetup').selectpicker('refresh');
}

function clear_movement_toolbox() {
  pipe_seperated_inserted_movs_string = '';

  document.getElementById('id-movement-loc-string').value = '';
  document.getElementById('id-add-hoc-move-dep-time').value = '';

  opts = document.getElementById('id-mov-traffic-type').options;
  for (var i = 0, opt; (opt = opts[i]); i++) {
    opt.selected = false;
  }
  selectElement((id = 'id-mov-traffic-type'), (valueToSelect = 'Express'));

  vhcleopts = document.getElementById('id-movement-vehicle-type').options;
  for (var i = 0, opt; (opt = vhcleopts[i]); i++) {
    opt.selected = false;
  }
  $('#id-movement-vehicle-type').selectpicker('refresh');

  locs_opts = document.getElementById('id-loc-lookup-list').options;
  for (var i = 0, opt; (opt = locs_opts[i]); i++) {
    opt.selected = false;
  }
  $('#id-loc-lookup-list').selectpicker('refresh');

  document.getElementById('id-captured-movements').innerText = '';
}

function undo_movement_capture() {
  let __spltr = '\u00A0\u00A0\u00A0\u00A0' + ' | ' + '\u00A0\u00A0\u00A0\u00A0';
  let __lst = pipe_seperated_inserted_movs_string.split(__spltr);
  let __last_item = __lst.pop();
  pipe_seperated_inserted_movs_string = __lst.join(__spltr);
  document.getElementById('id-captured-movements').innerText =
    pipe_seperated_inserted_movs_string;
}

function capture_movement() {
  let str_list = [];
  let __lcstrng = $('#id-movement-loc-string').val();

  __lcstrng = __lcstrng.replace('->', '.');
  __lcstrng = __lcstrng.replace('>', '.');
  __lcstrng = __lcstrng.replace(':', '');

  let __traffictype = $('#id-mov-traffic-type').val();
  let __vehicle = $('#id-movement-vehicle-type').val();
  let dep_day = $('#id-week-day-for-movement').val();
  let buffer = $('#id-changeover-connection-time').val();

  if (buffer == '') {
    buffer = '15';
    document.getElementById('id-changeover-connection-time').value = 15;
  }

  if (__traffictype == '') {
    __traffictype = 'Express';
    selectElement('id-mov-traffic-type', 'Express');
  }

  if (dep_day == '') {
    dep_day = 'Mon';
    selectElement('id-week-day-for-movement', 'Mon');
  }

  if (__vehicle.length == 0) {
    __vehicle = '1';
  }

  if (__lcstrng == '' || __lcstrng == undefined) {
    return false;
  }

  str_list.push(__lcstrng);

  let dt = __lcstrng.split('.').pop();
  if (!$.isNumeric(dt)) {
    dt = $('#id-add-hoc-move-dep-time').val();
  }

  if (dt == '') {
    return false;
  }

  let day = $('#id-week-day-for-movement').val();
  dt = ('0000' + dt).slice(-4);

  let __hrs = Number(dt.slice(0, 2));
  let __mins = Number(dt.slice(-2));

  if (__traffictype != '' && __lcstrng.indexOf(__traffictype) < 0) {
    str_list.push(__traffictype);
  }

  str_list.push(__vehicle);
  str_list.push(day);
  str_list.push(('0000' + dt).slice(-4));

  let spltr = ' | ';

  if (pipe_seperated_inserted_movs_string != '') {
    pipe_seperated_inserted_movs_string =
      pipe_seperated_inserted_movs_string +
      spltr +
      str_list.join(window.loc_string_spliter);
  } else {
    pipe_seperated_inserted_movs_string = str_list.join(
      window.loc_string_spliter
    );
  }

  spltr = '\u00A0\u00A0\u00A0\u00A0' + ' | ' + '\u00A0\u00A0\u00A0\u00A0';
  document.getElementById('id-movement-loc-string').value = '';

  return true;
}

function insert_selected_movement() {
  let __dct_adjusted_chart_data = py2js(
    (str_func_name = 'insert_movements'),
    (dct_params = {
      page_num: window.currPage,
      movement_id: $('#id-movement-bucket').val(),
    }),
    (url = '/drivers'),
    (async = false)
  );

  if ('err_message' in __dct_adjusted_chart_data) {
    create_popup(
      (title = 'Movement creation failed!'),
      (message = __dct_adjusted_chart_data.err_message)
    );

    set_default_title();
    scrollIntoDiv((getElementById = 'id-all_maps'));
    return;
  }

  refresh_unplanned_movs();
  load_driver_shift_chart((dct_chart_data = __dct_adjusted_chart_data));

  set_default_title();
  scrollIntoDiv((getElementById = 'id-all_maps'));
}

function insert_movements() {
  let __lcstrng = $('#id-movement-loc-string').val();

  if (__lcstrng == '' || __lcstrng == undefined) {
    return false;
  }

  __lcstrng = __lcstrng.replace('->', '.');
  __lcstrng = __lcstrng.replace('>', '.');
  __lcstrng = __lcstrng.replace(':', '');

  let __traffictype = $('#id-mov-traffic-type').val();
  let __vehicle = $('#id-movement-vehicle-type').val();
  let dep_day = $('#id-week-day-for-movement').val();
  let buffer = $('#id-changeover-connection-time').val();
  let tu_dest = $('#id-tu-dest').val();

  if (buffer == '') {
    buffer = '15';
    document.getElementById('id-changeover-connection-time').value = 15;
  }

  if (__traffictype == '') {
    __traffictype = 'Express';
    selectElement('id-mov-traffic-type', 'Express');
  }

  if (dep_day == '') {
    dep_day = 'Mon';
    selectElement('id-week-day-for-movement', 'Mon');
  }

  if (__vehicle.length == 0) {
    __vehicle = '1';
  }

  hidePopup((id = 'id-insert-movement-frame'));

  set_title('Creating movement ...');
  let dct_adjusted_chart_data = py2js(
    (str_func_name = 'insert_movements'),
    (dct_params = {
      page_num: window.currPage,
      co_con_time: buffer,
      traffic_type: __traffictype,
      loc_string: __lcstrng,
      vehicle: __vehicle,
      dep_day: dep_day,
      tu_dest: tu_dest,
    }),
    (url = '/insert-movements')
  );

  if ($.isEmptyObject(dct_adjusted_chart_data)) {
    set_default_title();
    scrollIntoDiv((getElementById = 'id-all_maps'));
    return;
  }

  if (dct_adjusted_chart_data.code === 400) {
    create_popup(
      (title = 'Create movement'),
      (message = dct_adjusted_chart_data.error)
    );
    set_default_title();
    return;
  }

  load_driver_shift_chart((dct_chart_data = dct_adjusted_chart_data));

  set_default_title();
  scrollIntoDiv((getElementById = 'id-all_maps'));
}

function unfix_shift_rightclick() {
  let dct_fix_shft = py2js(
    (str_func_name = 'toggle_fixing_shifts'),
    (dct_params = {}),
    (url = '/drivers'),
    (async = false)
  );

  if (!$.isEmptyObject(dct_fix_shft)) {
    load_driver_shift_chart(
      (dct_chart_data = dct_fix_shft),
      (render_to = 'chart-assign-drivers')
    );
  }

  set_default_title();
}

// function draw_tour_rightclick() {
//   let tour_draw_data = py2js(
//     (str_func_name = 'draw_tour'),
//     (dct_params = {}),
//     (url = '/drivers')
//   );

//   document.getElementById('id-display-shift-on-map').style.display = 'block';

//   $('#id-tours-map').remove();
//   $('#parent-draw-tour-rightclick').append(
//     '<div id="id-tours-map" style="width: 50vw; height: 50vh; vertical-align: top"></div>'
//   );

//   load_map((tours_vis_data = tour_draw_data), (id = 'id-tours-map'));
// }

async function refresh_shift_rightclick() {
  let dct_shift_data = sync_post(
    '/refresh-shift',
    (dct_params = { pagenum: window.currPage })
  );

  if (dct_shift_data.code === 400) {
    let await_status1 = await create_popup_async(
      (title = 'Refresh failed'),
      (message = dct_shift_data.error)
    );
    if (await_status1 === 'OK') {
      return;
    }
  }

  let await_status = 'OK';
  if (dct_shift_data.notifications !== '') {
    await_status = await create_popup_async(
      (title = 'Refresh status'),
      (message = dct_shift_data.notifications)
    );
  }

  if (await_status === 'OK') {
    if (!$.isEmptyObject(dct_shift_data)) {
      insert_disp_drag_full();
      load_driver_shift_chart((dct_chart_data = dct_shift_data.chart_data));
    }
  }
}

function draw_tour(shift_id = 0) {
  if (document.getElementById('id-remove-map').checked) {
    return;
  }

  clean_up_map();

  if (window.selected_tours_to_take_action.length == 0) {
    return;
  }

  let tour_draw_data = py2js(
    (str_func_name = 'draw_tour'),
    (dct_params = {
      shift_id: shift_id,
    }),
    (url = '/drivers')
  );

  clear_selected_tours_to_take_action();
  load_map((tours_vis_data = tour_draw_data));
}

function update_weekly_schedule() {
  set_title('Applying weekly changes ...');

  let __days = $('#id-wkdays-to-apply-weekly-chg').val();
  if (__days.length > 0) {
    py2js(
      (str_func_name = 'update_weekly_schedule'),
      (dct_params = { weekdays: __days }),
      (url = '/drivers')
    );
  }

  set_default_title();
}

function delete_movement_rightclick() {
  let mid = Number(
    document.getElementById('id-right-clicked-movement-id').value
  );
  dct_user_changes['dct_shiftchanges'][mid] = 'Recycle bin';
  process_user_changes();
}

function preview_report() {
  window.open('/view_report_wait/' + 'rightclicked', '_blank');
}

function preview_driver_report(page_drivers = false, full_weekPlan = false) {
  let drivers_str = 'LION Driver Plan';
  if (full_weekPlan === true) {
    drivers_str = 'FullPlan';
  } else {
    if (page_drivers === false) {
      drivers_str = window.selected_tours_to_take_action.join(';');

      if (drivers_str === '') {
        drivers_str = 'LION Driver Plan';
        // create_popup(title = 'No shift selected', message = 'Please select a shift to display driver plan!');
        // return;
      }
    }
  }

  window.open('/view_report_wait/' + drivers_str, '_blank');
  clear_selected_tours_to_take_action();
}

function export_driver_plan_rightclick() {
  py2js(
    (str_func_name = 'gen_driver_report'),
    (dct_params = { get_right_click_id: true, page_num: window.currPage }),
    (url = '/drivers')
  );
}

function show_driver_plan_with_day() {
  document.getElementById(
    'id-gen-driver-plan-with-day-selection'
  ).style.display = 'block';
}

function gen_driver_report_day_selection() {
  set_title('Generating driver report ...');
  document.getElementById(
    'id-gen-driver-plan-with-day-selection'
  ).style.display = 'none';
  let days = $('#id-wkdays-to-gen-driver-plan').val();

  let status = sync_post(
    '/gen-driver-report',
    (dct_params = {
      weekdays: days,
      publish: document.getElementById('id-chkbox-publish-driver-plan').checked,
      no_pdf: document.getElementById('id-chkbox-pdf-report').checked == false,
    })
  );

  create_popup(
    (title = 'Driver report generation status!'),
    (message = status.message)
  );

  // py2js(
  //   (str_func_name = 'gen_driver_report'),
  //   (dct_params = {
  //     weekdays: days,
  //     publish: document.getElementById('id-chkbox-publish-driver-plan').checked,
  //     no_pdf: document.getElementById('id-chkbox-pdf-report').checked == false,
  //   }),
  //   (url = '/drivers')
  // );

  set_default_title();
}

function export_page_driver_report() {
  set_title('Generating driver report ...');

  py2js(
    (str_func_name = 'gen_driver_report'),
    (dct_params = { page_num: window.currPage }),
    (url = '/drivers')
  );

  clear_selected_tours_to_take_action();
  set_default_title();
}

function clear_selected_tours_to_take_action() {
  window.selected_tours_to_take_action = [];
}

function show_popup(id) {
  let popupDiv = document.getElementById(id);
  popupDiv.style.display = 'none';

  // let toolbox = document.getElementById('id-toolbox-div');

  const toolbox_actions = {
    'id-insert-movement-frame': disp_mov_win_div,
    'id-insert-driver-frame': disp_driver_win_div,
    'id-manage-runtimes': disp_runtime_win_div,
    'id-save-shift-data': disp_save_shift_data_win,
    'id-insert-location-frame': disp_loc_win_div,
  };

  const actions = {
    'id-manage-optimization': disp_opt_win_div,
  };

  if (toolbox_actions.hasOwnProperty(id)) {
    // toolbox.style.display = 'block';
    toolbox_actions[id]();
  } else {
    actions[id]();
  }
}

function hidePopup(id) {
  var popupDiv = document.getElementById(id);
  popupDiv.style.display = 'none';
}
