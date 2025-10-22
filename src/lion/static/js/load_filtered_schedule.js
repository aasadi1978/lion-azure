// load_filtered_schedule
function load_filtered_shift_data() {
  let changeovers = $('#id-changeovers').val();
  if (changeovers.length > 0) {
    load_changeover_shifts((changeovers = changeovers));
    return;
  }

  let selected_shift_strng = $('#id-shift-string').val();
  let tour_locations = $('#id-search-by-loc').val();
  let vehicle_types = $('#id-search-by-vehicle').val();

  let Vehicles = [];
  for (var i = 0; i < vehicle_types.length; i++) {
    Vehicles.push(vehicle_types[i]);
  }

  let shifts = [];
  let shiftsids = [];

  for (var i = 0; i < selected_shift_strng.length; i++) {
    shiftsids = selected_shift_strng[i].split(',');

    for (var j = 0; j < shiftsids.length; j++) {
      shifts.push(shiftsids[j]);
    }
  }

  let _dct_params = {
    // weekday: wkday,
    loc_codes: tour_locations,
    shifts: shifts,
    // changeovers: changeovers,
    Vehicles: Vehicles,
    page_num: 1,
    // full_week_clicked: full_week_clicked,
  };

  let status = save_filter_params(_dct_params);

  if (status.code === 200) {
    window.location.href = '/';
  } else {
    create_popup(
      (title = 'INFO'),
      (message = 'Failed to save filter parameters')
    );
  }
}
