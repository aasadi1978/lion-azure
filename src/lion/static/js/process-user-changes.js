function show_notification() {
  const swalWithBootstrapButtons = Swal.mixin({
    customClass: {
      confirmButton: 'btn btn-success',
    },
    buttonsStyling: false,
  });

  swalWithBootstrapButtons
    .fire({
      title: 'WARNING!',
      text: notifications,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'OK',
      reverseButtons: true,
    })
    .then((result) => {
      if (result.value) {
        let status_reject_user_changes = py2js(
          (str_func_name = 'reject_user_changes'),
          (dct_params = {
            page_num: window.currPage,
          }),
          (url = '/drivers')
        );
        insert_disp_drag_full();
        load_driver_shift_chart((dct_chart_data = status_reject_user_changes));
      }
    });
}

async function process_user_changes() {
  set_title('Verifying connection ...');

  try {
    const status = await connection_status();
    if (status !== 'OK') {
      create_popup(
        'Connection Error',
        `Unable to connect to the server. Status: ${status}`
      );
      set_default_title();
      return;
    }
  } catch (error) {
    create_popup(
      'Connection Error',
      `Unable to connect to the server. ${error}`
    );
    set_default_title();
    return;
  }

  set_title('Processing changes ...');

  let status_process_user_changes = py2js(
    (str_func_name = 'process_user_changes'),
    (dct_params = {
      page_num: window.currPage,
      dct_user_changes: window.dct_user_changes,
    }),
    (url = '/drivers')
  );

  if (!$.isEmptyObject(status_process_user_changes)) {
    let notifications = status_process_user_changes.notifications;
    if (notifications == undefined || notifications.length == 0) {
      notifications = '';
    }

    let __popup = status_process_user_changes.popup;
    if (__popup == undefined || __popup.length == 0) {
      __popup = '';
    }

    let _changeover_timechange_msg =
      status_process_user_changes.changeover_timechange_msg;

    if (
      _changeover_timechange_msg == undefined ||
      _changeover_timechange_msg.length == 0
    ) {
      _changeover_timechange_msg = '';
    }

    let _empty_movement_msg = status_process_user_changes.empty_movement_msg;

    if (_empty_movement_msg == undefined || _empty_movement_msg.length == 0) {
      _empty_movement_msg = '';
    }

    if (_empty_movement_msg != '') {
      create_popup((title = 'Notification'), (message = _empty_movement_msg));

      let status_reject_user_changes = py2js(
        (str_func_name = 'reject_user_changes'),
        (dct_params = {
          page_num: window.currPage,
        }),
        (url = '/drivers')
      );
      load_driver_shift_chart((dct_chart_data = status_reject_user_changes));
      return;
    }

    if (_changeover_timechange_msg != '') {
      create_popup(
        (title = 'Notification'),
        (message = _changeover_timechange_msg)
      );

      clear_user_changes();
      set_default_title();
      // scrollIntoDiv(getElementById = 'id-all_maps')
      return;
    }

    if (__popup != '') {
      create_popup((title = 'Operation cancelled!'), (message = __popup));
      // insert_disp_drag_full()
      load_driver_shift_chart((dct_chart_data = status_process_user_changes));
    } else {
      if (notifications != '') {
        const swalWithBootstrapButtons = Swal.mixin({
          customClass: {
            cancelButton: 'btn btn-danger',
            confirmButton: 'btn btn-success',
          },
          buttonsStyling: false,
        });

        swalWithBootstrapButtons
          .fire({
            title: 'WARNNING!',
            text: notifications,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Accept',
            cancelButtonText: 'Reject',
            reverseButtons: true,
          })
          .then((result) => {
            if (result.value) {
              let status_accepted_chart_data = py2js(
                (str_func_name = 'accept_user_changes'),
                (dct_params = { page_num: window.currPage }),
                (url = '/drivers')
              );

              if ($.isEmptyObject(status_accepted_chart_data)) {
                create_popup(
                  (title = 'Change accpetence failed'),
                  (message = 'No chart data was returned!')
                );
                scrollIntoDiv((getElementById = 'id-all_maps'));
                return;
              }

              if ('current' in status_accepted_chart_data) {
                insert_disp_drag_double();
                load_driver_shift_chart(
                  (dct_chart_data = status_accepted_chart_data.current),
                  (render_to = 'chart-assign-drivers')
                );
                load_driver_shift_chart(
                  (dct_chart_data = status_accepted_chart_data.scn),
                  (render_to = 'chart-assign-drivers-tobe')
                );
              } else {
                insert_disp_drag_full();
                load_driver_shift_chart(
                  (dct_chart_data = status_accepted_chart_data)
                );
              }
            } else if (result.dismiss === Swal.DismissReason.cancel) {
              let status_reject_user_changes = py2js(
                (str_func_name = 'reject_user_changes'),
                (dct_params = {
                  page_num: window.currPage,
                }),
                (url = '/drivers')
              );
              insert_disp_drag_full();
              load_driver_shift_chart(
                (dct_chart_data = status_reject_user_changes)
              );
            }
          });
      } else {
        if ('current' in status_process_user_changes) {
          insert_disp_drag_double();
          load_driver_shift_chart(
            (dct_chart_data = status_process_user_changes.current),
            (render_to = 'chart-assign-drivers')
          );
          load_driver_shift_chart(
            (dct_chart_data = status_process_user_changes.scn),
            (render_to = 'chart-assign-drivers-tobe')
          );
        } else {
          insert_disp_drag_full();
          load_driver_shift_chart(
            (dct_chart_data = status_process_user_changes)
          );
        }
      }
    }

    clear_user_changes();
    set_default_title();
    scrollIntoDiv((getElementById = 'id-all_maps'));
  }
}
