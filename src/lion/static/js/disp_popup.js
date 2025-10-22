function disp_popup(
  message = '',
  title = 'Info',
  type = 'info',
  async = false
) {
  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  let output_py2js;
  if (message != '') {
    $ajax = $.ajax({
      type: 'POST',
      url: `${apiBaseURI}/disp_popup`,
      async: async,
      cache: false,
      data: {
        requested_data: JSON.stringify({
          message: message,
          title: title,
          type: type,
        }),
      },
      dataType: 'json',
      success: function (response) {
        output_py2js = response;
      },
      error: function (xhr, ajaxOptions, thrownError) {
        console.log(thrownError);
        console.log(xhr);
        console.log(ajaxOptions);
        console.log(str_func_name);
      },
    });
  }
}
