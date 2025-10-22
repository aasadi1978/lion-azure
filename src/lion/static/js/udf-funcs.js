function getRandom(length) {
  return Math.floor(Math.random() * length);
}

function getRandomSample(array, size) {
  var length = array.length;

  if (size > length) {
    size = length;
  }

  for (var i = size; i--; ) {
    var index = getRandom(length);
    var temp = array[index];
    array[index] = array[i];
    array[i] = temp;
  }

  return array.slice(0, size);
}

function seconds2hm(seconds) {
  // Converts seconds to hh:mm format

  const totalMinutes = Math.ceil(seconds / 60); // Round up to account for remaining seconds
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  return `${hours.toString().padStart(2, '0')}:${minutes
    .toString()
    .padStart(2, '0')}`;
}

// function seconds2hm(d) {
//   // Converts seconds to hh:mm format
//   d = Number(d);
//   var h = Math.floor(d / 3600);
//   var m = Math.floor(d % 3600 / 60);
//   var s = Math.floor(d % 3600 % 60);
//
//   if (s > 0) {
//     m += 1
//     if (m >= 60) {
//       h += 1
//       m = m - 60
//     }
//   }
//
//   return ('0' + h).slice(-2) + ":" + ('0' + m).slice(-2)
// };

function lion_setAttributes(el, attrs) {
  for (var key in attrs) {
    el.setAttribute(key, attrs[key]);
  }
  return el;
}

// RGBA color values are an extension of RGB color values with an alpha channel -
// which specifies the opacity for a color. An RGBA color value is specified with:
// rgba(red, green, blue, alpha). The alpha parameter is a number between 0.0 (fully transparent) and 1.0 (fully opaque).
function hexToRgbA(hex, opacity_alpha = 1) {
  var c;
  if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
    c = hex.substring(1).split('');
    if (c.length == 3) {
      c = [c[0], c[0], c[1], c[1], c[2], c[2]];
    }
    c = '0x' + c.join('');
    return (
      'rgba(' +
      [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') +
      ',' +
      opacity_alpha +
      ')'
    );
  }
  throw new Error('Bad Hex');
}

function monoChromatic(n, hue = '#00FFFF') {
  // hue = ['orange', 'red', 'yellow', 'green', 'purple', 'pink', '#00FFFF', 'blue', 'monochrome']
  // https://randomcolor.lllllllllllllllll.com/
  return randomColor({ hue: hue, count: n });
}

//Generate random colors
function chart_colors(n, reshuffle = false) {
  // lionColors = {
  //   cyan: "#00ffff",
  //   red: "#ff0000",
  //   orange: "#ff8c00",
  //   blue: "#0000ff",
  //   olive: "#808000",
  //   purple: "#800080",
  //   yellow: "#ffff00",
  //   aqua: "#00ffff",
  //   azure: "#f0ffff",
  //   beige: "#f5f5dc",
  //   black: "#000000",
  //   brown: "#a52a2a",
  //   darkcyan: "#008b8b",
  //   darkblue: "#00008b",
  //   darkgrey: "#a9a9a9",
  //   darkgreen: "#006400",
  //   darkkhaki: "#bdb76b",
  //   darkmagenta: "#8b008b",
  //   darkolivegreen: "#556b2f",
  //   darkorchid: "#9932cc",
  //   darkred: "#8b0000",
  //   darksalmon: "#e9967a",
  //   darkviolet: "#9400d3",
  //   fuchsia: "#ff00ff",
  //   gold: "#ffd700",
  //   green: "#008000",
  //   indigo: "#4b0082",
  //   khaki: "#f0e68c",
  //   lightblue: "#add8e6",
  //   lightcyan: "#e0ffff",
  //   lightgreen: "#90ee90",
  //   lightgrey: "#d3d3d3",
  //   lightpink: "#ffb6c1",
  //   lightyellow: "#ffffe0",
  //   lime: "#00ff00",
  //   magenta: "#ff00ff",
  //   maroon: "#800000",
  //   navy: "#000080",
  //   darkorange: "#ffa500",
  //   pink: "#ffc0cb",
  //   violet: "#800080",
  //   silver: "#c0c0c0"
  // };

  let myColors = [
    '#00ffff',
    '#ff0000',
    '#ff8c00',
    '#0000ff',
    '#808000',
    '#800080',
    '#00ffff',
    '#f0ffff',
    '#f5f5dc',
    '#000000',
    '#a52a2a',
    '#008b8b',
    '#00008b',
    '#a9a9a9',
    '#006400',
    '#bdb76b',
    '#8b008b',
    '#556b2f',
    '#9932cc',
    '#8b0000',
    '#e9967a',
    '#9400d3',
    '#ff00ff',
    '#ffd700',
    '#008000',
    '#4b0082',
    '#f0e68c',
    '#add8e6',
    '#e0ffff',
    '#90ee90',
    '#d3d3d3',
    '#ffb6c1',
    '#ffffe0',
    '#00ff00',
    '#ff00ff',
    '#800000',
    '#000080',
    '#ffa500',
    '#ffc0cb',
    '#800080',
    '#c0c0c0',
    '#ffff00',
  ];

  if (reshuffle == true) {
    myColors = shuffle(myColors);
  }

  // let nColors = myColors.length

  if (n <= 42) {
    return myColors.slice(0, n);
  }

  // TRULY RAN­DOM COL­ORS
  // other option: randomColor({luminosity: 'dark', count: n});
  //other option randomColor({luminosity: 'light',count: n});
  let luminosity = 'dark';
  return randomColor({ hue: 'random', luminosity: luminosity, count: n });
}

//Generate random colors
function color_per_item(mylist) {
  let n = mylist.length;

  if (n > 0) {
    let myColors = [
      '#00ffff',
      '#ff0000',
      '#ff8c00',
      '#0000ff',
      '#808000',
      '#800080',
      '#ffff00',
      '#00ffff',
      '#f0ffff',
      '#f5f5dc',
      '#000000',
      '#a52a2a',
      '#008b8b',
      '#00008b',
      '#a9a9a9',
      '#006400',
      '#bdb76b',
      '#8b008b',
      '#556b2f',
      '#9932cc',
      '#8b0000',
      '#e9967a',
      '#9400d3',
      '#ff00ff',
      '#ffd700',
      '#008000',
      '#4b0082',
      '#f0e68c',
      '#add8e6',
      '#e0ffff',
      '#90ee90',
      '#d3d3d3',
      '#ffb6c1',
      '#ffffe0',
      '#00ff00',
      '#ff00ff',
      '#800000',
      '#000080',
      '#ffa500',
      '#ffc0cb',
      '#800080',
      '#c0c0c0',
    ];

    let item_color = {};
    let idx = 0;
    let cols = [];

    if (n <= 42) {
      cols = myColors.slice(0, n);
    } else {
      // TRULY RAN­DOM COL­ORS
      // other option: randomColor({luminosity: 'dark', count: n});
      //other option randomColor({luminosity: 'light',count: n});
      let luminosity = 'dark';
      cols = randomColor({ hue: 'random', luminosity: luminosity, count: n });
    }

    if (cols.length > 0) {
      for (let itm of mylist) {
        item_color[itm] = cols[idx];
        idx += 1;
      }
    }

    return item_color;
  }

  return null;
}

function shuffle(array) {
  array.sort(() => Math.random() - 0.5);
  return array;
}

function jsSum(array) {
  if (array == undefined) {
    return 0;
  }
  if (array.length == 1) {
    return array[0];
  }
  if (array.length >= 2) {
    return array.reduce(function (a, b) {
      return a + b;
    }, 0);
  } else {
    return 0;
  }
}

function jsAvg(array) {
  return jsSum(array) / array.length;
}

function sortArraywithLables(arrayData, arrayLabel) {
  arrayOfObj = arrayLabel.map(function (d, i) {
    return {
      label: d,
      data: arrayData[i] || 0,
    };
  });

  sortedArrayOfObj = arrayOfObj.sort(function (a, b) {
    // return b.data>a.data; this should be used in FireFox
    return b.data - a.data;
  });

  newArrayLabel = [];
  newArrayData = [];
  sortedArrayOfObj.forEach(function (d) {
    newArrayLabel.push(d.label);
    newArrayData.push(d.data);
  });

  return { newLabel: newArrayLabel, newData: newArrayData };
}

function str2UTC(str_date = 'yyyy-mm-dd hh:mm') {
  // Return the number of milliseconds between a specified datetime (dt) and midnight January 1 1970
  let d = str_date.split(' ');
  let ymd = d[0].split('-');
  let hm = d[1].split(':');

  let utc = Date.UTC(ymd[0], ymd[1] - 1, ymd[2], hm[0], hm[1], 0);

  return utc;
}

function utc2hhmm(myDuration) {
  return moment.utc(myDuration).format('HH:mm');
  // return moment.utc(myDuration).local().format("DD/MM/YYYY HH:mm");
}

function utc2str(myDuration) {
  return moment.utc(myDuration).local().format('DD/MM/YYYY HH:mm');
}

function update_log(message, type = 'Info', url = '') {
  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  if (!url.startsWith('/')) {
    url = '/update_log';
  }

  $.ajax({
    type: 'POST',
    url: `${apiBaseURI}${url}`,
    async: false,
    data: {
      javascript_data: JSON.stringify({
        type: type,
        message: message,
      }),
    },
    dataType: 'json',
    success: function (response) {
      if (response['code'] == 400) {
        alert(
          'An error occured when trying to update log file:\n' +
            response['message']
        );
      }
    },
    error: function (xhr, ajaxOptions, thrownError) {
      dir(thrownError);
      dir(xhr);
      dir(ajaxOptions);
    },
  });
}

// url = "/restart_program"
function abort(url) {
  const swalWithBootstrapButtons = Swal.mixin({
    customClass: {
      confirmButton: 'btn btn-success',
      cancelButton: 'btn btn-danger',
    },
    buttonsStyling: false,
  });

  swalWithBootstrapButtons
    .fire({
      title: 'Are you sure?',
      text: "You won't be able to revert this and all calculations will be lost!",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: 'Yes, abort it!',
      cancelButtonText: 'No, cancel!',
      reverseButtons: true,
    })
    .then((result) => {
      if (result.value) {
        $.post(
          (url = url),
          (data = {
            abort: JSON.stringify(true),
          }),
          (success = function (response) {
            return;
          })
        );
      } else if (
        /* Read more about handling dismissals below */
        result.dismiss === Swal.DismissReason.cancel
      ) {
        swalWithBootstrapButtons.fire(
          'Cancelled',
          'Abortion was canceled!',
          'error'
        );
      }
    });
}

function removeElement(array, elem) {
  var index = array.indexOf(elem);
  if (index > -1) {
    array.splice(index, 1);
  }

  return array;
}

function swal_popup(message = '', title = 'Info', icon = 'error') {
  // Do not forget to add the folloing to top of your html file
  // <script src="//cdn.jsdelivr.net/npm/sweetalert2@11"></script>
  Swal.fire({
    title: title,
    text: message,
    icon: icon,
    confirmButtonColor: '#FF6600',

    // background:,
    customClass: {
      title: 'fancy-alert-title',
      content: 'fancy-alert-content',
    },
  });
}

function un_hide_div(elementId) {
  const x = document.getElementById(elementId);
  if (x.style.display === 'none') {
    x.style.display = 'block';
  } else {
    x.style.display = 'none';
  }
}

function scrollIntoDiv(elementId) {
  const myContainer = document.getElementById(elementId);
  myContainer.scrollIntoView({ behavior: 'smooth' });
}
// window.location.hash = document.getElementById(elementId)

async function showInput(title = '') {
  try {
    const { value: userInput } = await Swal.fire({
      text: title || 'Enter your value',
      input: 'number',
      inputAttributes: {
        autocapitalize: 'off',
      },
      showCancelButton: true,
      confirmButtonText: 'Save',
      customClass: {
        confirmButton: 'btn btn-primary',
        cancelButton: 'btn btn-default',
      },
      buttonsStyling: false,
      inputValidator: (value) => {
        if (!value) {
          return 'You need to enter something!';
        }
      },
    });

    if (userInput) {
      return userInput;
    } else {
      console.log('User cancelled');
      return undefined;
    }
  } catch (error) {
    Swal.fire('Error!', 'Something went wrong.', `${error}`);
    return undefined;
  }
}

async function showSwalInput(title = '') {
  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  try {
    const result = await Swal.fire({
      text: title,
      input: 'password',
      inputAttributes: {
        autocapitalize: 'off',
      },
      showCancelButton: true,
      confirmButtonText: 'Validate',
      customClass: {
        confirmButton: 'btn btn-primary',
        cancelButton: 'btn btn-default',
      },
      buttonsStyling: false,
      showLoaderOnConfirm: true,
      preConfirm: (password) => {
        return fetch(`${apiBaseURI}/check-scn-password/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            requested_data: JSON.stringify({ pwd: password }),
          }),
        })
          .then((response) => {
            if (!response.ok) {
              throw new Error(response.statusText);
            }
            return response.json();
          })
          .then((data) => {
            if (data.status === false) {
              throw new Error(data.message);
            }
          })
          .catch((error) => {
            Swal.showValidationMessage(`Request failed: ${error}`);
          });
      },
      allowOutsideClick: () => !Swal.isLoading(),
    });

    if (result.value) {
      return true; // Password validated
    } else {
      return false; // User cancelled
    }
  } catch (error) {
    return false; // Validation failed
  }
}

// async function validatePassword() {
//   const is_pwd_valid = await showSwalInput('Enter your password');
//   console.log('Password validation result:', is_pwd_valid);
// }

// validatePassword();

// function showSwalInput(title=''){
//   Swal.fire({
//     title: title,
//     input: 'text',
//     inputAttributes: {
//       autocapitalize: 'off'
//     },
//     showCancelButton: true,
//     confirmButtonText: 'Look up',
//     customClass: {
//       confirmButton: 'btn btn-primary',
//       cancelButton: 'btn btn-default'
//     },
//     buttonsStyling: false,
//     showLoaderOnConfirm: true,
//     preConfirm: (login) => {
//       return fetch(`//api.github.com/users/${login}`)
//         .then(response => {
//           if (!response.ok) {
//             throw new Error(response.statusText)
//           }
//           return response.json()
//         })
//         .catch(error => {
//           Swal.showValidationMessage(
//             `Request failed: ${error}`
//           )
//         })
//     },
//     allowOutsideClick: () => !Swal.isLoading()
//   }).then((result) => {
//     if (result.value) {
//       Swal.fire({
//         title: `${result.value.login}'s avatar`,
//         imageUrl: result.value.avatar_url
//       })
//     }
//   })
// };

// function showSwal(type) {
//   if (type == 'basic') {
//     Swal.fire({
//       title: 'Here is a message!',
//       customClass: {
//         confirmButton: 'btn btn-info'
//       },
//       buttonsStyling: false

//     })} else if (type == 'title-and-text') {

//       Swal.fire({
//         title: 'The Internet?',
//         text: 'That thing is still around?',
//         type: 'question',
//         customClass: {
//           confirmButton: 'btn btn-primary'
//         },
//         buttonsStyling: false,
//       })

//     } else if (type == 'success-message') {

//       Swal.fire({
//         position: 'center',
//         type: 'success',
//         title: 'Good job!',
//         showConfirmButton: false,
//         timer: 1500
//       })

//     } else if (type == 'warning-message-and-confirmation') {
//       const swalWithBootstrapButtons = Swal.mixin({
//         customClass: {
//           confirmButton: 'btn btn-success',
//           cancelButton: 'btn btn-danger'
//         },
//         buttonsStyling: false
//       })

//       swalWithBootstrapButtons.fire({
//         title: 'Are you sure?',
//         text: "You won't be able to revert this!",
//         type: 'warning',
//         showCancelButton: true,
//         confirmButtonText: 'Yes, delete it!',
//         cancelButtonText: 'No, cancel!',
//         reverseButtons: true
//       }).then((result) => {
//         if (result.value) {
//           swalWithBootstrapButtons.fire(
//             'Deleted!',
//             'Your file has been deleted.',
//             'success'
//           )
//         } else if (
//           /* Read more about handling dismissals below */
//           result.dismiss === Swal.DismissReason.cancel
//         ) {
//           swalWithBootstrapButtons.fire(
//             'Cancelled',
//             'Your imaginary file is safe :)',
//             'error'
//           )
//         }
//       })
//     } else if (type == 'warning-message-and-cancel') {
//       Swal.fire({
//         title: 'Are you sure?',
//         text: "You won't be able to revert this!",
//         type: 'warning',
//         showCancelButton: true,
//         customClass: {
//           confirmButton: 'btn btn-success',
//           cancelButton: 'btn btn-danger'
//         },
//         buttonsStyling: false,
//         confirmButtonText: 'Yes, delete it!'
//       }).then((result) => {
//         if (result.value) {
//           Swal.fire(
//             'Deleted!',
//             'Your file has been deleted.',
//             'success'
//           )
//         }
//       })
//     } else if (type == 'custom-html') {
//       Swal.fire({
//         title: '<strong>HTML <u>example</u></strong>',
//         type: 'info',
//         html: 'You can use <b>bold text</b>, ' +
//           '<a href="//sweetalert2.github.io">links</a> ' +
//           'and other HTML tags',
//         showCloseButton: true,
//         showCancelButton: true,
//         customClass: {
//           confirmButton: 'btn btn-success',
//           cancelButton: 'btn btn-danger'
//         },
//         buttonsStyling: false,
//         focusConfirm: false,
//         confirmButtonText: '<i class="fa fa-thumbs-up"></i> Great!',
//         confirmButtonAriaLabel: 'Thumbs up, great!',
//         cancelButtonText: '<i class="fa fa-thumbs-down"></i>',
//         cancelButtonAriaLabel: 'Thumbs down'
//       })
//     } else if (type == 'auto-close') {
//       let timerInterval
//       Swal.fire({
//         title: 'Auto close alert!',
//         html: 'I will close in <strong></strong> milliseconds.',
//         timer: 2000,
//         onBeforeOpen: () => {
//           Swal.showLoading()
//           timerInterval = setInterval(() => {
//             Swal.getContent().querySelector('strong')
//               .textContent = Swal.getTimerLeft()
//           }, 100)
//         },
//         onClose: () => {
//           clearInterval(timerInterval)
//         }
//       }).then((result) => {
//         if (
//           /* Read more about handling dismissals below */
//           result.dismiss === Swal.DismissReason.timer
//         ) {
//           console.log('I was closed by the timer')
//         }
//       })
//     } else if (type == 'input-field') {
//       Swal.fire({
//         title: 'Submit your Github username',
//         input: 'text',
//         inputAttributes: {
//           autocapitalize: 'off'
//         },
//         showCancelButton: true,
//         confirmButtonText: 'Look up',
//         customClass: {
//           confirmButton: 'btn btn-primary',
//           cancelButton: 'btn btn-default'
//         },
//         buttonsStyling: false,
//         showLoaderOnConfirm: true,
//         preConfirm: (login) => {
//           return fetch(`//api.github.com/users/${login}`)
//             .then(response => {
//               if (!response.ok) {
//                 throw new Error(response.statusText)
//               }
//               return response.json()
//             })
//             .catch(error => {
//               Swal.showValidationMessage(
//                 `Request failed: ${error}`
//               )
//             })
//         },
//         allowOutsideClick: () => !Swal.isLoading()
//       }).then((result) => {
//         if (result.value) {
//           Swal.fire({
//             title: `${result.value.login}'s avatar`,
//             imageUrl: result.value.avatar_url
//           })
//         }
//       })
//     }
//   };

async function swal_with_bootstrap_buttons(
  title = 'Info',
  message = 'This is test message',
  type = 'warning',
  confirmButtonText = 'OK',
  cancelButtonText = 'Cancel'
) {
  const swlbuttns = Swal.mixin({
    customClass: {
      cancelButton: 'btn btn-danger',
      confirmButton: 'btn btn-success',
    },
    buttonsStyling: false,
  });

  let swlbuttns_fire = await swlbuttns.fire({
    title: title,
    text: message,
    icon: type,
    showCancelButton: true,
    confirmButtonText: confirmButtonText,
    cancelButtonText: cancelButtonText,
    reverseButtons: true,
  });

  return swlbuttns_fire;
}

async function create_popup_with_decision(
  title = 'Info',
  message = 'This is test message',
  type = 'warning', // other options are "success", "error", "warning", "info" or "question"
  confirmButtonText = 'OK',
  cancelButtonText = 'Cancel'
) {
  let status = await swal_with_bootstrap_buttons(
    title,
    message,
    type,
    confirmButtonText,
    cancelButtonText
  )
    .then((result) => {
      if (result.value) {
        return 'OK';
      } else if (result.dismiss == 'cancel') {
        return 'Cancelled';
      }
    })
    .catch((error) => {
      return `Error: ${error}`;
    });

  return status;
}

function create_popup(title = 'Info', message = '') {
  //Types: "success", "error", "warning", "info" or "question"
  const __swalWithBootstrapButtons2 = Swal.mixin({
    customClass: {
      confirmButton: 'btn btn-primary',
    },
    buttonsStyling: false,
  });

  if (message.length > 250) {
    console.log(message);
    message = message.substring(0, 250) + ' (in console) ...';
  }

  __swalWithBootstrapButtons2.fire({
    title: title && title.trim().length > 0 ? title : 'Info',
    text: message,
    // html: `<pre style="text-align:left;">${message}</pre>`,
    showCancelButton: false,
    confirmButtonText: 'OK',
  });
}

async function create_popup_async(
  title = 'Info',
  message = '',
  icon = 'info',
  type = 'info'
) {
  //Types: "success", "error", "warning", "info" or "question"

  if (message.length > 250) {
    console.log(message);
    message = message.substring(0, 250) + ' (in console) ...';
  }

  let status = await Swal.mixin({
    customClass: {
      confirmButton: 'btn btn-primary',
    },
    buttonsStyling: false,
  })
    .fire({
      title: title,
      text: message,
      showCancelButton: false,
      confirmButtonText: 'OK',
    })
    .then((result) => {
      if (result.value) {
        return 'OK';
      } else if (result.dismiss == 'cancel') {
        return 'Cancelled';
      }
    })
    .catch((error) => {
      return `Error: ${error}`;
    });

  return status;
}

// async function swal_with_bootstrap_buttons(title = 'Info',
//   message = 'This is test message',
//   type = 'warning',
//   confirmButtonText = 'OK',
//   cancelButtonText = 'Cancel') {

//     // let val = false
//     const swlbuttns = Swal.mixin({
//       customClass: {
//         cancelButton: 'btn btn-danger',
//         confirmButton: 'btn btn-success',
//       },
//       buttonsStyling: false,
//     });

//     let swlbuttns_fire = await swlbuttns.fire({
//       title: title,
//       text: message,
//       type: type,
//       showCancelButton: true,
//       confirmButtonText: confirmButtonText,
//       cancelButtonText: cancelButtonText,
//       reverseButtons: true,
//     })

//     swlbuttns_fire.then(({name, id})=> console.log({name, id}))

//     // swlbuttns_fire.then(function(response) {
//     //   return response.json();
//     // })

//     // return !!swlbuttns_fire.value;

// };

// async function create_popup_with_decision(title = 'Info',
// message = 'This is test message',
// type = 'warning', // other options are "success", "error", "warning", "info" or "question"
// confirmButtonText = 'OK',
// cancelButtonText = 'Cancel') {

//   status = await new Promise((resolve)=>{
//     swal_with_bootstrap_buttons(title = title,
//       message = message,
//       type = type,
//       confirmButtonText = confirmButtonText,
//       cancelButtonText = cancelButtonText
//     ).then(() => {
//         resolve('OK')
//     }).catch(error => {
//         resolve(error)
//     });
//   });

//   alert(status)
// }
