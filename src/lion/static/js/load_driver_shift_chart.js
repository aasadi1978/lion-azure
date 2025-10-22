// var imported = document.createElement('script');
// imported.src = '/udf-funcs.js';
// document.head.appendChild(imported);
// Define your custom right-click functionality here

function attachRightClickToPoints(chart) {
  chart.series.forEach((series) => {
    series.points.forEach((p) => {
      if (p.to == 'Shift') {
        p.graphic.element.addEventListener('contextmenu', function (e) {
          e.preventDefault();

          var contextMenu = document.getElementById(
            'id-customContextMenu-shift'
          );
          contextMenu.style.display = 'block';
          contextMenu.style.top = e.pageY + 'px';
          contextMenu.style.left = e.pageX + 'px';

          set_right_click_id(p.object_id);
          document.getElementById('id-driver-to-add-note').value = p.driver;

          // Hide the menu when clicking elsewhere
          document.addEventListener(
            'click',
            function () {
              contextMenu.style.display = 'none';
            },
            { once: true }
          );
        });

        return;
      }

      if (typeof p.object_id == 'number' && !(p.traffic_type == 'Empty')) {
        //Add right click menus to shift
        p.graphic.element.addEventListener('contextmenu', function (e) {
          e.preventDefault();

          var contextMenu = document.getElementById(
            'id-customContextMenu-movement'
          );
          contextMenu.style.display = 'block';
          contextMenu.style.top = e.pageY + 'px';
          contextMenu.style.left = e.pageX + 'px';

          set_right_click_id(p.object_id);

          document.getElementById('id-right-clicked-movement-id').value =
            p.object_id;
          document.getElementById('id-right-clicked-movement-lhid').value =
            p.loc_string;
          document.getElementById(
            'id-right-clicked-movement-traffic-type'
          ).value = p.traffic_type;
          document.getElementById(
            'id-right-clicked-movement-vehicle-type'
          ).value = p.vehicle;
          document.getElementById('id-right-clicked-movement-depday').value =
            p.depday;
          document.getElementById('id-right-clicked-movement-tu-dest').value =
            p.tu;

          // Hide the menu when clicking elsewhere
          document.addEventListener(
            'click',
            function () {
              contextMenu.style.display = 'none';
            },
            { once: true }
          );
        });
      }
    });
  });
}

function is_chart_data_ok(dct_chart_data) {
  let valid_chart = true;

  if (dct_chart_data == undefined || dct_chart_data == {}) {
    valid_chart = false;
  }

  valid_chart = valid_chart && 'options' in dct_chart_data;
  if (valid_chart) {
    valid_chart = valid_chart && 'drivers' in dct_chart_data;

    if (valid_chart) {
      let opt = dct_chart_data.options;
      valid_chart =
        'n_drivers' in opt &&
        opt.n_drivers > 0 &&
        'n_all_drivers' in opt &&
        opt.n_all_drivers > 2 &&
        'dict_footprint' in opt &&
        opt.dict_footprint != {} &&
        opt.operators &&
        opt.operators != [] &&
        opt.n_all_drivers &&
        opt.n_all_drivers > 2;
    }
  }
  return valid_chart;
}

async function validate_chart_data(dct_chart_data) {
  let chart_data_is_valid = await is_chart_data_ok(dct_chart_data);
  if (chart_data_is_valid) {
    return dct_chart_data;
  }

  let status_cold_start_notification = await create_popup_async(
    (title = 'Loading issue'),
    (message =
      'We ran into an issue when loading the schedule. Please wait for a retry ... You will be notified when it is done.'),
    (type = 'Info')
  );

  if (status_cold_start_notification == 'OK') {
    let status_cold_start = sync_post('/cold-schedule-reload/', {});

    if (status_cold_start.code == 400) {
      create_popup((title = 'Error'), (message = status_cold_start.error));
    } else {
      dct_chart_data = status_cold_start.chart_data;

      if (is_chart_data_ok(dct_chart_data)) {
        create_popup(
          (title = 'Info'),
          (message =
            'Validation: Schedule reloaded. Please try again in a few seconds.')
        );

        return dct_chart_data;
      }
    }
  }

  return {};
}

async function load_driver_shift_chart(
  dct_chart_data = undefined,
  render_to = 'chart-assign-drivers'
) {
  startHealthCheck();
  if ('message' in dct_chart_data) {
    create_popup((title = 'Chart data'), (message = dct_chart_data.message));
    return;
  }

  if ('notifications' in dct_chart_data && dct_chart_data.notifications != '') {
    create_popup(
      (title = 'Chart notifications'),
      (message = dct_chart_data.notifications)
    );
    return;
  }

  dct_chart_data = await validate_chart_data(dct_chart_data);
  if (dct_chart_data == {}) {
    console.log('dct_chart_data was not provided or is not valid');
    return;
  }

  // resetDoubleClick();

  let show_labels_flag = document.getElementById('id-show-labels').checked;
  if (render_to == 'chart-assign-drivers') {
    options = dct_chart_data.options;

    dct_chart_data_latest = { ...dct_chart_data };
    refresh_options(options);

    if (window.currPage >= window.n_pages) {
      document.getElementById('btn-Next').disabled = true;
    } else {
      document.getElementById('btn-Next').disabled = false;
    }
    if (window.currPage <= 1) {
      document.getElementById('btn-Previous').disabled = true;
    } else {
      document.getElementById('btn-Previous').disabled = false;
    }

    clear_selected_tours_to_take_action();
  }

  let zoom_type = '';
  if (document.getElementById('id-enable-zoom-switch').checked) {
    zoom_type = 'xy';
  }

  driver_chart = Highcharts.chart({
    chart: {
      renderTo: document.getElementById(render_to),
      animation: false,
      // gridLineWidth:0,
      // margin: [120, 120, 120, 120],
      type: 'xrange',
      marginTop: 150,
      marginRight: 50,
      marginBottom: 120,
      marginLeft: 450,
      // backgroundColor:'#999999'
      // plotBackgroundColor: 'lightgray',
      zoomType: zoom_type,
      events: {
        load: function () {
          attachRightClickToPoints(this);
        },
      },
    },

    // credits: {
    //   enabled: true
    // },

    credits: {
      text: 'fedex.com',
      href: 'https://www.fedex.com/',
    },

    accessibility: {
      enabled: true,
    },

    title: {
      text: dct_chart_data.shift_name,
      style: {
        fontSize: '22px',
        fontWeight: 'bold',
        color: '#4D148C',
        fontFamily: 'FedEx Sans',
      },
    },

    // subtitle: {
    //   text: weekday,
    //   style: {
    //     color: '#ff6200'
    //   },
    // },

    // caption: {
    //   text: "&#169; Copyright 2024 Road Network Planning &amp; Engineering | FedEx Express Europe",
    //   align: "center",
    //   style: {
    //     color: "black",
    //   },
    // },

    tooltip: {
      // enabled: document.getElementById('id-disp-tooltip-chkbox').checked,
      backgroundColor: '#dedede',
      borderColor: '#071330',
      borderWidth: 3,

      // headerFormat: '<span style="font-size: 14px; font-weight:bold fill-color: blue"> Shift information </span><br/>',
      // pointFormat:
      //   '<div>\
      //     <span >loc_string: {point.loc_string} </span><br/> \
      //         <span >shift: {point.driver} </span><br/> \
      //         <span >operator: {point.operator} </span><br/> \
      //         <span >vehicle: {point.vehicle} </span><br/> \
      //     </div>',

      formatter: function () {
        if (this.point.loc_string === undefined) {
          return false;
        }

        document.getElementById('id-tooltip-info').style.display = 'block';

        let __str = '';
        let __spc = '\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0';
        if (this.point.to.substr(0, 5) == 'Shift') {
          __str = __str + __spc + 'Shift: ' + this.point.driver;
          __str = __str + __spc + 'vehicle: ' + this.point.vehicle;
          __str = __str + __spc + 'operator: ' + this.point.operator;
          __str =
            __str + __spc + 'time_utilisation: ' + this.point.time_utilisation;
          __str = __str + __spc + 'Start: ' + this.point.dt1;
          __str = __str + __spc + 'End: ' + this.point.dt2;
          __str = __str + __spc + 'Running days: ' + this.point.rdays;
          __str = __str + __spc + 'shift_id: ' + this.point.object_id;
          // __str = __str + __spc + 'strID: ' + this.point.strID

          if (this.point.mouseover_info != '') {
            __str = __str + __spc + 'NOTE: ' + this.point.mouseover_info;
          }
        } else {
          if (this.point.label == 'BRK') {
            __str = __str + __spc + 'Departure: ' + this.point.dt1;
            __str = __str + __spc + 'Arrival: ' + this.point.dt2;
            __str = __str + __spc + 'Lane: ' + this.point.label;
            __str = __str + __spc + 'Shift: ' + this.point.driver;
            return false;
          }

          __str = __str + __spc + 'Loc_string: ' + this.point.loc_string;
          __str = __str + __spc + 'vehicle: ' + this.point.vehicle;
          __str = __str + __spc + 'Departure: ' + this.point.dt1;
          __str = __str + __spc + 'Arrival: ' + this.point.dt2;
          __str = __str + __spc + 'Lane: ' + this.point.label;
          __str = __str + __spc + 'Leg: ' + this.point.Leg;
          __str = __str + __spc + 'TU Dest: ' + this.point.tu;
          __str = __str + __spc + 'TrafficType: ' + this.point.traffic_type;
          __str = __str + __spc + 'Shift: ' + this.point.driver;
          __str = __str + __spc + 'mileage: ' + this.point.mileage;
          __str =
            __str + __spc + 'Runtime (excl. Turn.): ' + this.point.driving_time;
          __str = __str + __spc + 'id: ' + this.point.object_id;
          __str = __str + __spc + 'strID: ' + this.point.strID;
        }

        document.getElementById('id-tooltip-info').innerText = __str;
        driver_chart.userOptions.title.text = __str;

        return false;
        // }
      },

      style: {
        // fontFamily: 'Segoe UI, Tahoma'
        // display: (document.getElementById('id-disp-tooltip-chkbox').checked ? 'block' : 'none'),
        width: '700px',
        // fontSize: '12px',
        lineHeight: '25px',
        fontWeight: 'bold',
        paddingLeft: 7,
        paddingRight: 5,
        paddingTop: 5,
        // fontFamily: 'sans-serif'
      },

      // formatter: function () {
      //   return s + '<br/>' + point.t1 + ': ' + point.t2 + 'm';
      // },
    },

    // tooltip: {
    //   backgroundColor: '#fcfcfc',
    //   borderColor: '#c9c9c9',
    //   borderWidth: 1,
    //   // formatter: function () {
    //   //   var s = '<b>' + this.x + '</b>';
    //   //   $.each(this.points, function (i, point) {
    //   //     s += '<br/><span style="font-size: 20px">' + point.y + '</span>';
    //   //   });
    //   //   return s;
    //   // },
    //   shadow: false,
    //   shared: true,
    //   style: {
    //     fontFamily: 'Segoe UI, Tahoma',
    //     fontSize: '12px',
    //     lineHeight: '21px',
    //     paddingLeft: 7,
    //     paddingRight: 5,
    //     paddingTop: 5
    //   },
    // },

    // events: {
    //   dbclick: function (e) {
    //     alert('Double clicked.');
    //   },
    // },

    plotOptions: {
      series: {
        minPointLength: 15,
        animation: false,
        dataLabels: {
          style: {
            fontSize: '0.95em',
            fontFamily: 'FedEx Sans',
            color: 'black',
          },
          allowOverlap: true, // to enforce all labels to be visible
          enabled: show_labels_flag,
          format: '{point.label}', //  linehaul_id
          align: 'center',
          inside: true,
          // events: {
          //   dblClick: function (e) {
          //     run_actions_on_dblClick(e, this);
          //   },
          // },
        },

        dragDrop: {
          draggableX: true,
          draggableY: true,
          // dragMinY: 0,
          // dragMaxY: dct_chart_data.drivers.length,
          dragMinX: dct_chart_data.xAxis_range[0],
          dragMaxX: dct_chart_data.xAxis_range[1],
          liveRedraw: true,
          groupBy: 'groupId', // Group data points with the same groupId
        },
        point: {
          events: {
            dragStart: function (e) {
              if (!window.connection_healthy) {
                create_popup(
                  'Connection lost',
                  'Cannot drag while disconnected.'
                );
                e.preventDefault();
                return;
              }
            },

            drag: function (e) {
              if (window.connection_healthy) {
                const result = round_time_to_nearest_5min(
                  (timestamp = e.newPoint.x)
                );
                var lbl = e.target.label;
                e.target.label = lbl.split(':')[0] + ':' + result.slice(11, 16);
              }
            },

            //   var status = 'Dragging "' +
            //     (this.name || this.object_id) + '". ' + e.numNewPoints
            //   ' point(s) selected.';

            //   // If more than one point is being updated, see
            //   // e.newPoints for a hashmap of these. Here we just add
            //   // info if there is a single point.

            //   if (e.newPoint) {
            //     status += ' New x/x2/y: ' + utc2hhmm(e.newPoint.x) +
            //       '/' + utc2hhmm(e.newPoint.x2) + '/' + e_newPoint_y;
            //   }

            //   setDragStatus(status = status);
            // },

            mouseOver: function (e) {
              // e.browserEvent.preventDefault();
              // let m_id = e.target.object_id;
              let m_id = e.target.object_id;
              let id = e.target.id;
              let shift_id = e.target.shift_id;
              let dct_m = dct_chart_data.dct_bar_data_movements[id];
              let dct_shift = dct_chart_data.dct_bar_data_shifts[shift_id];

              let __mouseover_text = '';
              let shift_mouseover_info = dct_shift.mouseover_info;

              if (m_id == shift_id) {
                __mouseover_text = dct_shift.remark;
              } else {
                __mouseover_text = dct_m.mouseover_info;
              }

              document.getElementById(
                'id-shift-information-label'
              ).style.color = 'black';
              if (shift_mouseover_info != '') {
                document.getElementById(
                  'id-shift-information-label'
                ).innerText = shift_mouseover_info + '; ' + __mouseover_text;
                document.getElementById(
                  'id-shift-information-label'
                ).style.color = 'red';
              } else {
                document.getElementById(
                  'id-shift-information-label-parent'
                ).style.display = 'block';
                document.getElementById(
                  'id-shift-information-label'
                ).innerText = __mouseover_text;
              }
            },

            drop: function (e) {
              if (e.newPoint.x == undefined && e.newPoint.x2 != undefined) {
                let newPointId = e.newPointId;
                e.newPoint.x = e.origin.points[newPointId].point.x;
                e.newPoint.y = e.origin.points[newPointId].point.y;
              }

              if (e.newPoint.x2 == undefined && e.newPoint.x != undefined) {
                let newPointId = e.newPointId;
                e.newPoint.x2 = e.origin.points[newPointId].point.x2;
                e.newPoint.y = e.origin.points[newPointId].point.y;
              }

              let dragged_to_shift_id = dct_chart_data.shift_ids[e.newPoint.y];

              let __chgtime_on_drag = true; //document.getElementById('id-chg-time-on-drop').checked

              if (dragged_to_shift_id == undefined) {
                dragged_to_shift_id = this.shift_id;
              }

              if (this.shift_id == dragged_to_shift_id && __chgtime_on_drag) {
                const __new_date_time = round_time_to_nearest_5min(
                  (timestamp = e.newPoint.x)
                );
                let dct_changed_time = {
                  datetime: __new_date_time,
                  movement_id: this.object_id,
                  shift_id: this.shift_id,
                };

                window.dct_user_changes['dct_timechanges'] = dct_changed_time;
              } else {
                if (!(this.shift_id == dragged_to_shift_id)) {
                  window.dct_user_changes['dct_shiftchanges'][this.object_id] =
                    dragged_to_shift_id;
                }
              }
              process_user_changes();
              return;
            },

            dblClick: function (e) {
              run_actions_on_dblClick(e, this);
            },

            click: function (e) {
              // let be = e.browserEvent
              // if (be.which === 3) {

              //   $("#contextMenu")
              //       .css({
              //           top: be.clientY + "px",
              //           left: be.clientX + "px"
              //       })
              //       .show();

              //   $("#menuOption1").off('click').on('click', function() {
              //       // Add functionality for Option 1 here
              //       $("#contextMenu").hide();
              //   });

              let t_id = e.point.options.shift_id;
              let m_id = e.point.options.object_id;
              let is_shift =
                this.to.substr(0, 5) == 'Shift' || e.point.to == 'Shift';

              if (
                !window.selected_movements_to_take_action.includes([t_id, m_id])
              ) {
                window.selected_movements_to_take_action.push([t_id, m_id]);
              }

              if (is_shift) {
                if (e.ctrlKey) {
                  if (!window.selected_tours_to_take_action.includes(t_id)) {
                    window.selected_tours_to_take_action.push(t_id);
                  }
                } else {
                  window.selected_tours_to_take_action = [t_id];
                }

                // !(document.getElementById('id-select-multiple').checked) &&
                if (
                  window.selected_tours_to_take_action.length == 1 &&
                  !e.ctrlKey
                ) {
                  draw_tour((shift_id = e.point.options.shift_id));
                }
              }
            },
          },
        },
      },
    },

    xAxis: [
      {
        // opposite: true,
        type: 'datetime',
        min: dct_chart_data.xAxis_range[0],
        max: dct_chart_data.xAxis_range[1],
        tickInterval: 3600 * 1000, // Hourly
        dateTimeLabelFormats: {
          day: '%H%H',
        },
        labels: {
          style: {
            color: 'black',
            fontWeight: 'bold',
            fontSize: '0.9em',
            fontFamily: 'FedEx Sans', //'Courier New',
          },
        },
      },
      {
        opposite: true,
        type: 'datetime',
        min: dct_chart_data.xAxis_range[0],
        max: dct_chart_data.xAxis_range[1],
        tickInterval: 3600 * 1000, // Hourly
        dateTimeLabelFormats: {
          day: '%H%H',
        },
        labels: {
          style: {
            color: 'black',
            fontSize: '0.9em',
            fontFamily: 'FedEx Sans', //'Courier New',
            fontWeight: 'bold',
          },
        },

        // title: {
        //   text: 'Schedule',
        //   style: {
        //     color: 'black',
        //     fontSize: '10px',
        //   },
        // },
      },
    ],

    yAxis: [
      {
        // title: {
        //   text: 'Drivers'
        // },
        title: '',
        // min: 0,
        // gridLineWidth: 0,
        // max: dct_chart_data.drivers.length,
        categories: dct_chart_data.drivers,
        labels: {
          events: {
            click: function () {
              navigator.clipboard.writeText(this.value);
            },
          },
          formatter: function () {
            if (dct_chart_data.changed_drivers.includes(this.value)) {
              return (
                '<span style="fill: red; font-weight:bold">' +
                this.value +
                '</span>'
              );
            }

            if (dct_chart_data.new_drivers.includes(this.value)) {
              return (
                '<span style="fill: green; font-weight:bold">' +
                this.value +
                '</span>'
              );
            }

            if (dct_chart_data.removed_drivers.includes(this.value)) {
              return '<span style="fill: lightgray;">' + this.value + '</span>';
            }

            return this.value;
          },

          style: {
            color: 'black',
            fontWeight: 'bold',
            fontSize: '1em',
            fontFamily: 'FedEx Sans', // 'Courier New',
          },
        },
        // reversed: true
        // opposite: true
      },
      {
        // min: 0,
        title: 'Operators',
        gridLineWidth: 0,
        categories: dct_chart_data.driver_operators,
        labels: {
          formatter: function () {
            if (dct_chart_data.changed_drivers.includes(this.value)) {
              return (
                '<span style="fill: red; font-weight:bold">' +
                this.value +
                '</span>'
              );
            }

            if (dct_chart_data.new_drivers.includes(this.value)) {
              return (
                '<span style="fill: green; font-weight:bold">' +
                this.value +
                '</span>'
              );
            }

            if (dct_chart_data.removed_drivers.includes(this.value)) {
              return '<span style="fill: lightgray;">' + this.value + '</span>';
            }

            return this.value;
          },

          style: {
            color: 'black',
            fontWeight: 'bold',
            fontSize: '1em',
            fontFamily: 'FedEx Sans', // 'Courier New',
          },
        },
        // reversed: true,
        // opposite: true
      },
    ],

    exporting: {
      sourceWidth: 2500,
      sourceHeight: 2000,
      filename: 'Schedule-LION',
      chartOptions: {
        chart: {
          backgroundColor: '#f7f7f7',
          style: {
            fontFamily: 'FedEx Sans',
          },
          // plotBorderColor: '#346691',
          // plotBorderWidth: 2
        },
        plotOptions: {
          series: {
            dataLabels: {
              enabled: true,
              style: {
                fontSize: '0.8em',
                fontFamily: 'FedEx Sans',
                color: 'black',
              },
            },
          },
        },
        title: {
          style: {
            color: '#030303',
            fontSize: '22px',
          },
        },
        yAxis: [{ gridLineWidth: 0 }, { gridLineWidth: 0 }],
      },
      buttons: {
        contextButton: {
          menuItems: [
            {
              text: 'Navicon menu',
            },
            'separator',
            // {
            //   text: 'Apply weekly changes',
            //   onclick: function () {
            //     update_weekly_schedule()
            //   }
            // },
            {
              text: 'Export Schedule As',
              onclick: function () {
                show_popup((id = 'id-save-shift-data'));
              },
            },
            {
              text: 'KPI Report',
              onclick: function () {
                generate_kpi_report();
              },
            },
            // {
            //   text: 'SortBy ShiftLocString',
            //   onclick: function () {
            //     sort_by_tourLocString();
            //   },
            // },

            // {
            //   text: 'ViewFullscreen',
            //   onclick: function () {
            // this.fullscreen.open()
            // let chartDiv = document.getElementById('id-all_maps');
            // let chartAssignDrivers = document.getElementById('chart-assign-drivers');
            // chartAssignDrivers.style.width = '99vw';
            // chartDiv.classList.add('fullscreen');
            //   }
            // },
            // {
            //   text: 'ExitFullscreen',
            //   onclick: function () {
            //     var chartDiv = document.getElementById('id-all_maps');
            //     chartDiv.classList.remove('fullscreen');
            //     let chartAssignDrivers = document.getElementById('chart-assign-drivers');
            //     chartAssignDrivers.style.width = '96vw';
            //   }
            // },
            // 'separator',
            // {
            //   text: 'Add a note to shift',
            //   onclick: function () {
            //     disp_note_win_div()
            //   }
            // },
            'separator',
            {
              text: 'Add a movement (ctrl+M)',
              onclick: function () {
                show_popup((id = 'id-insert-movement-frame'));
              },
            },
            {
              text: 'Add/Modify driver (ctrl+D)',
              onclick: function () {
                show_popup((id = 'id-insert-driver-frame'));
              },
            },
            {
              text: 'Add/Modify a location (ctrl+L)',
              onclick: function () {
                clear_locations_toolbox();
                show_popup((id = 'id-insert-location-frame'));
              },
            },
            {
              text: 'Runtimes & Mileages(ctrl+R)',
              onclick: function () {
                show_popup((id = 'id-manage-runtimes'));
              },
            },
            'separator',
            {
              text: 'Preview page driver report',
              onclick: function () {
                preview_driver_report(
                  (page_drivers = false),
                  (full_weekPlan = false)
                );
              },
            },
            {
              text: 'Export page driver plan',
              onclick: function () {
                export_page_driver_report();
              },
            },
            {
              text: 'Export driver plan',
              onclick: function () {
                show_driver_plan_with_day();
              },
            },
            {
              text: 'Extract depature/arrivals',
              onclick: function () {
                let status = sync_post(
                  '/extract-dep-arrivals',
                  (dct_params = {})
                );
                create_popup(
                  (title = 'Extract depature/arrivals'),
                  (message = status.message)
                );
              },
            },
            'separator',
            // {
            //   text: 'Import latest master data',
            //   onclick: function () {
            //     import_databases();
            //   },
            // },
            {
              text: 'Import demo data',
              onclick: function () {
                import_default_sch_data();
              },
            },
            // {
            //   text: 'Export databases for distribution',
            //   onclick: function () {
            //     export_databases();
            //   },
            // },
            'separator',
            {
              text: 'Optimisation portal (ctrl+P)',
              onclick: function () {
                show_popup((id = 'id-manage-optimization'));
              },
            },
            // {
            //   text: "Refresh all",
            //   onclick: function () {
            //     run_optimization(
            //       (run_full_opt = true),
            //       (run_strategic_opt = false)
            //     );
            //   },
            // },
            // {
            //     text: 'Refresh current page',
            //     onclick: function () {
            //         run_optimization(
            //             (run_full_opt = false),
            //             (run_strategic_opt = false)
            //         )
            //     },
            // },
            'separator',
            {
              text: 'Export schedule (CTRL+E)',
              onclick: function () {
                export_local_schedule();
              },
            },
            {
              text: 'Export Schedule As',
              onclick: function () {
                show_popup((id = 'id-save-shift-data'));
              },
            },
            {
              text: 'Update suppliers',
              //This module updates suppliers, subcontractor name or Employed, based on suppliers.csv file
              //located in LION_HOME_PATH. The csv file has two columns, Shiftname, Supplier
              onclick: function () {
                update_suppliers();
              },
            },
            // {
            //   text: 'Toggle map',
            //   onclick: function () {
            //     document.getElementById('id-remove-map').click();
            //   },
            // },
            {
              text: 'Toggle labels',
              onclick: function () {
                document.getElementById('id-show-labels').click();
              },
            },
            {
              text: 'Toggle Zoom',
              onclick: function () {
                // if (!document.getElementById('id-enable-zoom-switch').checked){
                document.getElementById('id-enable-zoom-switch').click();
                toggle_zoom();
                // };
              },
            },
            {
              text: 'User manual',
              onclick: function () {
                open_user_manual();
              },
            },
            {
              text: 'Technical documentation',
              onclick: function () {
                open_technical_docs();
              },
            },
            {
              text: 'Log file',
              onclick: function () {
                preview_log_file();
              },
            },
            {
              text: 'Refresh shift indices (Reboot)',
              onclick: function () {
                refresh_shift_index();
              },
            },
          ],
        },
      },
    },
    series: [
      {
        // name: 'Schedule',
        showInLegend: false,
        cursor: 'move',
        yAxis: 0,
        data: dct_chart_data.tData,
        pattern: {
          patternIndex: 1,
        },
        states: {
          select: {
            color: '#0099CC',
          },
        },
        allowPointSelect: true,
      },
      {
        showInLegend: false,
        yAxis: 1,
        data: dct_chart_data.tData_operators,
      },
    ],
  });
}
