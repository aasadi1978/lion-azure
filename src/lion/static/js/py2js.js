function py2js(str_func_name = '', dct_params = {}, url = '', async = false) {
  let output_py2js;

  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  if (!url.startsWith('/')) {
    url = '/' + url;
  }

  $ajax = $.ajax({
    type: 'POST',
    url: `${apiBaseURI}${url}`,
    async: async, //async,
    cache: false,
    data: {
      requested_data: JSON.stringify({
        str_func_name: str_func_name,
        dct_params: dct_params,
      }),
    },
    dataType: 'json',
    success: function (response) {
      output_py2js = response;
    },

    error: function (xhr, ajaxOptions, thrownError) {
      console.log('Error in py2js:');
      console.log('----------------------------------------------');
      console.log(thrownError);
      console.log(xhr);
      console.log(ajaxOptions);
      console.log(str_func_name);
      console.log('----------------------------------------------');
    },
  });

  return output_py2js;
}

function async_post(endpoint, dct_params = {}) {
  let output_async_post;

  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  if (endpoint === '') {
    console.error('Endpoint is required for async_post');
    alert('Endpoint is required for async_post');
    return;
  }

  if (!endpoint.startsWith('/')) {
    endpoint = '/' + endpoint;
  }

  $ajax = $.ajax({
    type: 'POST',
    url: `${apiBaseURI}${endpoint}`,
    async: true,
    cache: false,
    data: {
      requested_data: JSON.stringify(dct_params),
    },
    dataType: 'json',
    success: function (response) {
      output_async_post = response;
    },

    error: function (xhr, ajaxOptions, thrownError) {
      console.log('----------------------------------------------');
      console.log('Error in async_post:');
      console.log(thrownError);
      console.log(xhr);
      console.log(ajaxOptions);
      console.log('----------------------------------------------');
    },
  });

  return output_async_post;
}

function sync_post(endpoint, dct_params = {}) {
  let output_sync_post;

  let config = window.options.api_config || loadConfig();
  const apiBaseURI = config.apiBaseURI ? config.apiBaseURI : '';

  if (endpoint === '') {
    console.error('Endpoint is required for sync_post');
    alert('Endpoint is required for sync_post');
    return;
  }

  if (!endpoint.startsWith('/')) {
    endpoint = '/' + endpoint;
  }

  $ajax = $.ajax({
    type: 'POST',
    url: `${apiBaseURI}${endpoint}`,
    async: false,
    cache: false,
    data: {
      requested_data: JSON.stringify(dct_params),
    },
    dataType: 'json',
    success: function (response) {
      output_sync_post = response;
    },

    error: function (xhr, ajaxOptions, thrownError) {
      console.log('----------------------------------------------');
      console.log('Error in sync_post:');
      console.log(thrownError);
      console.log(xhr);
      console.log(ajaxOptions);
      console.log('----------------------------------------------');
    },
  });

  return output_sync_post;
}
