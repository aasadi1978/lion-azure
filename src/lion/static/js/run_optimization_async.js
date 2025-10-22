async function run_optimization(endpoint = 'run-optimization') {
  run_optimization_async((endpoint = endpoint))
    .then(async (msg) => {
      document.getElementById('id-progressbar').style.display = 'none';

      if (msg != '') {
        let status = await create_popup_async(
          (title = 'Optimization success!'),
          (message = msg),
          (type = 'info')
        );
        if (status == 'OK') {
          window.location.href = '/';
        }
      }

      clear_user_changes();
      set_default_title();
    })
    .catch((errmsg) => {
      if (errmsg != '') {
        let status = create_popup_async(
          (title = 'Optimization failure!'),
          (message = errmsg),
          (type = 'ERROR')
        );
        if (status == 'OK') {
          window.location.href = '/';
        }
      }

      clear_user_changes();
      set_default_title();
    });
}

// https://euremars-lvl1-tss.emea.fedex.com:8001/spotfire/wp/OpenAnalysis?file=bcf2c83e-f3eb-4e57-9e50-82d360e4a09f
async function run_optimization_async(endpoint = '/run-optimization') {
  let msg = cache_optimization_params();
  if (msg != '') {
    create_popup(
      (title = 'Initialising optimization failed!'),
      (message = msg)
    );
    return;
  }

  hidePopup('id-manage-optimization');

  let div_progressbar = document.getElementById('id-progressbar');

  div_progressbar.style.display = 'block';
  document.getElementById('id-progress-bar-hidden').style.display = 'none';

  let optwkdays = $('#id-wkdays-to-copy-schedule').val();
  let vehicle_code = $('#id-vehicle-type-optimization').val();
  let excluded_locs = $('#id-loc-code-with-no-driver').val();
  let mip_solver = $('#id-select-mip-solver').val();
  let dblman_shift_dur = $('#id-dblman-shift-dur').val();
  let empty_downtime = $('#id-empty-mov-downtime').val();
  let maxdowntime_maxreposmin_II = $('#id-maxdowntime-maxrepostime-II').val();

  let n_top_closest_driver_loc = 10; //$('#id-top-closestdriverloc').val();

  set_title('Running optimization ...');

  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  return await new Promise((resolve, reject) => {
    $.post(
      `${apiBaseURI}${endpoint}`,
      {
        requested_data: JSON.stringify({
          // str_func_name: 'run_optimization',
          dct_params: {
            page_num: window.currPage,
            vehicle_code: vehicle_code,
            n_top_closest_driver_loc: n_top_closest_driver_loc,
            empty_downtime: empty_downtime,
            maxdowntime_maxreposmin_II: maxdowntime_maxreposmin_II,

            // Strategic optimization only
            apply_max_drivers_per_loc: document.getElementById(
              'id-apply-max-resource-per-loc'
            ).checked,

            // Strategic optimization only
            schedule_employed: document.getElementById('id-schedule-employed')
              .checked,

            // Strategic optimization only
            user_loaded_movs: document.getElementById(
              'id-user-loaded-movements'
            ).checked,

            // Strategic optimization only
            recalc_mileages_runtimes: document.getElementById(
              'id-recalc-runtimes-mileages'
            ).checked,

            // Strategic optimization only
            run_extended_optimization: document.getElementById(
              'id-run-extended-optimisation'
            ).checked,

            // Strategic optimization only
            excl_dblman: document.getElementById('id-excl-double-man-shifts')
              .checked,

            // Strategic optimization only
            schedule_dblman_movs: document.getElementById(
              'id-schedule-double-man-movements'
            ).checked,

            // Strategic optimization only
            identify_infeas_shifts: document.getElementById(
              'id-excl-infeas-shifts'
            ).checked,

            // show_comparison: true,

            // Strategic optimization only
            excluded_locs: excluded_locs,
            mip_solver: mip_solver,
            drivers: selected_tours_to_take_action,
            dblman_shift_dur: dblman_shift_dur,
            // Strategic optimization only
            optimization_weekdays: optwkdays,
          },
        }),
      },
      function (response) {
        if (response.code === 400) {
          if (response.message.length > 0) {
            reject(response.message);
            return response.message;
          }

          reject('');
          return '';
        }

        if ('current' in response) {
          insert_disp_drag_double();
          load_driver_shift_chart(
            (dct_chart_data = response.current),
            (render_to = 'chart-assign-drivers')
          );
          load_driver_shift_chart(
            (dct_chart_data = response.scn),
            (render_to = 'chart-assign-drivers-tobe')
          );

          if ('notification' in response) {
            resolve(response.notification);
            return response.notification;
          } else {
            resolve('');
            return '';
          }
        } else {
          if ($.isEmptyObject(response)) {
            reject('No response');
            return 'No response';
          }

          if (response.success != '') {
            console.log(response.success);
            resolve(response.success);
            return response.success;
          }

          if (response.failure != '') {
            console.log(response.failure);
            reject(response.failure);
            return response.failure;
          }
        }
      },
      'json'
    ).fail(function (xhr, textStatus, errorThrown) {
      set_default_title();
      console.log(errorThrown);
      console.log(xhr);
      console.log(textStatus);
      if (String(errorThrown).length > 0) {
        reject(String(errorThrown));
        return String(errorThrown);
      }
    });
  });
}
