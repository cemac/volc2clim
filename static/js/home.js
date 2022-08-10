'use strict';

/* --- global variables: --- */

/* url for running model: */
var model_url = '/model';

/* model parameters: */
var model_params = {
  'wavelengths': [550],
  'lat': 15.1,
  'year': 2021,
  'month': 1,
  'so2_mass': 18,
  'so2_height': 25,
  'tropo_height': 16,
  'so2_timescale': 8,
  'rad_eff': -21.5,
  'nc': 1
};
/* variable to indicate if parameters are o.k.: */
var model_params_ok = true;

/* input elements: */
var input_els = {
  'so2_mass': document.getElementById('so2_mass_input_value'),
  'so2_mass_error': document.getElementById('so2_mass_input_error'),
  'lat': document.getElementById('lat_input_value'),
  'lat_error': document.getElementById('lat_input_error'),
  'year': document.getElementById('year_input_value'),
  'year_error': document.getElementById('year_input_error'),
  'so2_height': document.getElementById('so2_height_input_value'),
  'so2_height_error': document.getElementById('so2_height_input_error'),
  'tropo_height': document.getElementById('tropo_height_input_value'),
  'tropo_height_error': document.getElementById('tropo_height_input_error'),
  'so2_timescale': document.getElementById('so2_timescale_input_value'),
  'so2_timescale_error': document.getElementById('so2_timescale_input_error'),
  'rad_eff': document.getElementById('rad_eff_input_value'),
  'rad_eff_error': document.getElementById('rad_eff_input_error'),
  'wavelengths_inputs': document.getElementById('wavelengths_inputs'),
  'wavelengths_error': document.getElementById('wavelengths_input_error'),
  'add_wavelength_button': document.getElementById('add_wavelength_button'),
  'remove_wavelength_button': document.getElementById('remove_wavelength_button'),
  'run_button': document.getElementById('run_model_button'),
  'run_button_display': null,
  'csv_download_button': document.getElementById('csv_download_button'),
  'nc_download_button': document.getElementById('nc_download_button')
};

/* plot config: */
var plot_vars = {
  /* main plot container element: */
  'plot_container_el': document.getElementById('content_plots'),
  'plot_container_el_display': null,
  /* model spinner element: */
  'model_spinner': document.getElementById('content_model_spinner'),
  /* saod time series plot element: */
  'saod_ts_el': document.getElementById('saod_ts_plot'),
  /* saod time series plot object: */
  'saod_ts_plot': null,
  /* saod time series plot variables: */
  'saod_ts_title': 'Global mean SAOD',
  'saod_ts_x_title': 'Date',
  'saod_ts_y_title': 'Stratospheric Aerosol<br>Optical Depth (SAOD)',
  'saod_ts_colors': ['#2ca02c', '#1f77b4', '#ff7f0e', '#cc79a7', '#999999',
                     '#f9e432', '#642133', '#ec3e00', '#fedd3f', '#4356b1'],
  /* contour plot element: */
  'saod_contour_el': document.getElementById('saod_contour_plot'),
  /* saod contour plot object: */
  'saod_contour_plot': null,
  /* saod contour plot variables: */
  'saod_contour_title': 'SAOD at 550nm',
  'saod_contour_x_title': 'Date',
  'saod_contour_y_title': 'Latitude (° North)',
  'saod_contour_cb_title': 'SAOD',
  'saod_contour_colorscale': [
    [0,'rgb(255,255,255)'],
    [0.3,'rgb(255,210,0)'],
    [0.6,'rgb(230,0,0)'],
    [1,'rgb(0,0,0)']
  ],
  /* fair rf time series plot element: */
  'fair_rf_ts_el': document.getElementById('fair_rf_ts_plot'),
  /* fair rf time series plot object: */
  'fair_rf_td_plot': null,
  /* fair rf time series plot variables: */
  'fair_rf_ts_title': 'Volcanic radiative forcing, W/m⁻²',
  'fair_rf_ts_x_title': 'Year',
  'fair_rf_ts_y_title': 'Effective radiative forcing at<br>top of atmosphere (W/m⁻²)',
  'fair_rf_ts_col': '#ff7f0e',
  'fair_rf_wo_ts_col': '#1f77b4',
  /* fair temp time series plot element: */
  'fair_temp_ts_el': document.getElementById('fair_temp_ts_plot'),
  /* fair temp time series plot object: */
  'fair_temp_td_plot': null,
  /* fair temp time series plot variables: */
  'fair_temp_ts_title': 'RCP4.5 temperature anomaly, K',
  'fair_temp_ts_x_title': 'Year',
  'fair_temp_ts_y_title': 'Temperature anomaly (K)',
  'fair_temp_ts_col': '#ff7f0e',
  'fair_temp_wo_ts_col': '#1f77b4'
};

/* html elements for statistics: */
var stats_els = {
  'stats_a_div': document.getElementById('content_model_stats_a'),
  'rf_peak_label': document.getElementById('stats_rf_peak_label'),
  'rf_peak_value': document.getElementById('stats_rf_peak_value'),
  'fair_temp_peak_label': document.getElementById('stats_fair_temp_peak_label'),
  'fair_temp_peak_value': document.getElementById('stats_fair_temp_peak_value')
};

/* model data: */
var model_data = null;

/* --- --- */

/* numeric check function: */
function check_numeric(name, value, value_min, value_max, check_int) {
  /* init output data: */
  var check_value = {
    'status': true,
    'message': null,
  };
  /* check empty: */
  if ((value == null) || (value == '')) {
    check_value['status'] = false;
    check_value['message'] = name + ' value is empty.';
  };
  /* check numeric: */
  if (isNaN(value) == true) {
    check_value['status'] = false;
    check_value['message'] = name + ' value is not numeric.';
  };
  /* check greater than min: */
  if (value < value_min) {
    check_value['status'] = false;
    check_value['message'] = name + ' value must not be less than ' +
                             value_min + '.';
  };
  /* check less than max: */
  if (value > value_max) {
    check_value['status'] = false;
    check_value['message'] = name + ' value must not be greater than ' +
                             value_max + '.';
  };
  /* check is integer: */
  if (check_int == true) {
    if (Number.isInteger(parseFloat(value)) == false) {
      check_value['status'] = false;
      check_value['message'] = name + ' value should be an integer.';
    };
  };
  /* return the output data: */
  return check_value;
}

/* text input validation function: */
function validate_text_input() {
  /* presume all o.k.: */
  model_params_ok = true;
  /* default input border color: */
  var input_border_ok = '#989898';
  /* input border color on error: */
  var input_border_err = '#ee3333';
  /* run button element: */
  var input_run_button = input_els['run_button'];
  /* so2 mass ... get value: */
  var so2_mass_el = input_els['so2_mass'];
  var so2_mass_value = so2_mass_el.value;
  /* error element: */
  var so2_mass_error_el = input_els['so2_mass_error'];
  so2_mass_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('Mass of SO₂', so2_mass_value, 0, 999999);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['so2_mass'] = parseFloat(so2_mass_value);
    so2_mass_error_el.style.display = 'none';
    so2_mass_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    so2_mass_error_el.innerHTML = check_value['message'];
    so2_mass_error_el.style.display = 'inline';
    so2_mass_el.style.borderColor = input_border_err;
  };
  /* if so2 mass i greater than 200, add message: */
  if ((model_params_ok == true) && (so2_mass_value > 20)) {
    so2_mass_error_el.innerHTML += ' We have a limited understanding of' +
                                   ' eruptions injecting >20 Tg SO2';
    so2_mass_error_el.style.display = 'inline';
    so2_mass_el.style.borderColor = input_border_err;
  };
  /* lat ... get value: */
  var lat_el = input_els['lat'];
  var lat_value = lat_el.value;
  /* error element: */
  var lat_error_el = input_els['lat_error'];
  lat_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('Latitude', lat_value, -90, 90);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['lat'] = parseFloat(lat_value);
    lat_error_el.style.display = 'none';
    lat_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    lat_error_el.innerHTML = check_value['message'];
    lat_error_el.style.display = 'inline';
    lat_el.style.borderColor = input_border_err;
  };
  /* year ... get value: */
  var year_el = input_els['year'];
  var year_value = year_el.value;
  /* error element: */
  var year_error_el = input_els['year_error'];
  year_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('Year', year_value, 1800, 2050, true);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['year'] = parseFloat(year_value);
    year_error_el.style.display = 'none';
    year_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    year_error_el.innerHTML = check_value['message'];
    year_error_el.style.display = 'inline';
    year_el.style.borderColor = input_border_err;
  };
  /* so2 height ... get value: */
  var so2_height_el = input_els['so2_height'];
  var so2_height_value = so2_height_el.value;
  /* error element: */
  var so2_height_error_el = input_els['so2_height_error'];
  so2_height_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('SO₂ injection height', so2_height_value, 0, 50);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['so2_height'] = parseFloat(so2_height_value);
    so2_height_error_el.style.display = 'none';
    so2_height_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    so2_height_error_el.innerHTML = check_value['message'];
    so2_height_error_el.style.display = 'inline';
    so2_height_el.style.borderColor = input_border_err;
  };
  /* tropo height ... get value: */
  var tropo_height_el = input_els['tropo_height'];
  var tropo_height_value = tropo_height_el.value;
  /* error element: */
  var tropo_height_error_el = input_els['tropo_height_error'];
  tropo_height_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('Tropopause height', tropo_height_value, 0, 50);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['tropo_height'] = parseFloat(tropo_height_value);
    tropo_height_error_el.style.display = 'none';
    tropo_height_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    tropo_height_error_el.innerHTML = check_value['message'];
    tropo_height_error_el.style.display = 'inline';
    tropo_height_el.style.borderColor = input_border_err;
  };
  /* so2 timescale ... get value: */
  var so2_timescale_el = input_els['so2_timescale'];
  var so2_timescale_value = so2_timescale_el.value;
  /* error element: */
  var so2_timescale_error_el = input_els['so2_timescale_error'];
  so2_timescale_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('SO₂ timescale', so2_timescale_value, 0.1, 50);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['so2_timescale'] = parseFloat(so2_timescale_value);
    so2_timescale_error_el.style.display = 'none';
    so2_timescale_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    so2_timescale_error_el.innerHTML = check_value['message'];
    so2_timescale_error_el.style.display = 'inline';
    so2_timescale_el.style.borderColor = input_border_err;
  };
  /* radiate efficiency / scale factor ... get value: */
  var rad_eff_el = input_els['rad_eff'];
  var rad_eff_value = rad_eff_el.value;
  /* error element: */
  var rad_eff_error_el = input_els['rad_eff_error'];
  rad_eff_error_el.innerHTML = '';
  /* check value: */
  var check_value = check_numeric('Scale factor', rad_eff_value, -50, -0.1);
  /* if o.k., store value: */
  if (check_value['status'] == true) {
    model_params['rad_eff'] = parseFloat(rad_eff_value);
    rad_eff_error_el.style.display = 'none';
    rad_eff_el.style.borderColor = input_border_ok;
  } else {
    /* not o.k.: */
    model_params_ok = false;
    rad_eff_error_el.innerHTML = check_value['message'];
    rad_eff_error_el.style.display = 'inline';
    rad_eff_el.style.borderColor = input_border_err;
  };
  /* wavelengths ... get values: */
  var wavelengths_els = document.getElementsByClassName(
    'wavelengths_input_value'
  );
  /* error element: */
  var wavelengths_error_el = input_els['wavelengths_error'];
  wavelengths_error_el.innerHTML = '';
  /* check values: */
  var wavelengths = [];
  for (var i = 0; i < wavelengths_els.length; i++) {
    var wavelength_value = wavelengths_els[i].value;
    var check_value = check_numeric(
      'Wavelength', wavelength_value, 1, 5000
    );
    /* if o.k., store value: */
    if (check_value['status'] == true) {
      wavelengths.push(parseFloat(wavelength_value));
      wavelengths_error_el.style.display = 'none';
      wavelengths_els[i].style.borderColor = input_border_ok;
    } else {
      /* not o.k.: */
      model_params_ok = false;
      wavelengths_error_el.innerHTML = check_value['message'];
      wavelengths_error_el.style.display = 'inline';
      wavelengths_els[i].style.borderColor = input_border_err;
      break;
    };
  };
  /* if all wavelengths are o.k.: */
  if (model_params_ok == true) {
    /* store the values: */
    model_params['wavelengths'] = wavelengths;
  };
  /* if parameters o.k., enable button: */
  if (model_params_ok == true) {
    input_run_button.removeAttribute('disabled');
  } else {
    input_run_button.setAttribute('disabled', true);
  };
};

/* select element input validation function: */
function validate_select_input() {
  /* month select element: */
  var month_el = document.getElementById('month_input_value');
  /* month value: */
  var month_value = month_el.options[month_el.selectedIndex].value;
  /* store the value: */
  model_params['month'] = parseFloat(month_value);
};

/* add wavelength input element: */
function add_wavelength_input() {
  /* wavelength inputs container: */
  var wavelengths_inputs = input_els['wavelengths_inputs'];
  /* get existing wavelength elements and count: */
  var wavelengths_els = document.getElementsByClassName(
    'wavelengths_input_value'
  );
  var wavelength_count = wavelengths_els.length;
  /* new element number / id: */
  var new_wavelength = wavelength_count + 1;
  /* add the new element: */
  var wavelength_input = document.createElement('input');
  wavelength_input.id = 'wavelengths' + new_wavelength  + '_input_value';
  wavelength_input.classList = 'wavelengths_input_value input_text ' +
                               'input_value_small';
  wavelength_input.type = 'text';
  wavelength_input.maxLength = 4;
  wavelength_input.name = 'wavelengths' + new_wavelength;
  wavelength_input.value = '550';
  wavelengths_inputs.appendChild(wavelength_input);
  /* add listeners to element ... add focus listener to select text: */
  wavelength_input.addEventListener('focus', wavelength_input.select);
  /* add change listener: */
  wavelength_input.addEventListener('input', validate_text_input);
  wavelength_input.addEventListener('propertychange', validate_text_input);
  /* enable remove button: */
  var remove_wavelength_el = document.getElementById(
    'remove_wavelength_button'
  );
  remove_wavelength_el.style.display = 'inline';
  /* focus the new element: */
  wavelength_input.focus();
  wavelength_input.select();
  /* remove add button if we get to 10 inputs: */
  if (wavelength_count > 8) {
    var remove_wavelength_el = document.getElementById(
      'add_wavelength_button'
    );
    remove_wavelength_el.style.display = 'none';
  };
};

/* remove wavelength input element: */
function remove_wavelength_input() {
  /* wavelength inputs container: */
  var wavelengths_inputs = input_els['wavelengths_inputs'];
  /* get existing wavelength elements and count: */
  var wavelengths_els = document.getElementsByClassName(
    'wavelengths_input_value'
  );
  var wavelength_count = wavelengths_els.length;
  /* get the final input element: */
  var wavelength_input = document.getElementById(
    'wavelengths' + wavelength_count + '_input_value'
  );
  /* remove the element: */
  wavelength_input.parentNode.removeChild(wavelength_input);
  /* disable remove button, if only one input left: */
  if (wavelength_count < 3) {
    var remove_wavelength_el = document.getElementById(
      'remove_wavelength_button'
    );
    remove_wavelength_el.style.display = 'none';
  };
  /* enable add button if less than 10 inputs: */
  if (wavelength_count < 11) {
    var remove_wavelength_el = document.getElementById(
      'add_wavelength_button'
    );
    remove_wavelength_el.style.display = 'inline';
  };

};

/* add input listeners: */
function add_listeners() {
  /* get all text input elements: */
  var input_values = document.getElementsByClassName('input_text');
  /* loop through values: */
  for (var i = 0; i < input_values.length; i++) {
    var input_value = input_values[i];
    /* add focus listener to select text: */
    input_value.addEventListener('focus', input_value.select);
    /* add change listener: */
    input_value.addEventListener('input', validate_text_input);
    input_value.addEventListener('propertychange', validate_text_input);
  };
  /* select inputs elements: */
  var input_selects = document.getElementsByClassName('input_select');
  /* loop through values: */
  for (var i = 0; i < input_selects.length; i++) {
    var input_select = input_selects[i];
    /* add change listener: */
    input_select.addEventListener('input', validate_select_input);
  };
  /* add run button listener: */
  var input_run_button = input_els['run_button'];
  /* add click listener: */
  input_run_button.addEventListener('click', run_model);
  /* add csv download button listener: */
  var input_csv_download = input_els['csv_download_button'];
  /* add click listener: */
  input_csv_download.addEventListener('click', get_csv_data);
  /* add netcdf download button listener: */
  var input_nc_download = input_els['nc_download_button'];
  /* add click listener: */
  input_nc_download.addEventListener('click', get_nc_data);
  /* add listeners for wavelength add and remove buttons: */
  var add_wavelength_button = input_els['add_wavelength_button'];
  add_wavelength_button.addEventListener('click', add_wavelength_input);
  var remove_wavelength_button = input_els['remove_wavelength_button'];
  remove_wavelength_button.addEventListener('click', remove_wavelength_input);
};

/* element hiding function: */
function hide_elements() {
  /* plot containiner element: */
  var plot_container_el = plot_vars['plot_container_el'];
  /* get display value: */
  plot_vars['plot_container_el_display'] = plot_container_el.style.display;
  /* hide the element: */
  plot_container_el.style.display = 'none';
};

/* data plotting function: */
function plot_data() {
  /* check for null data: */
  if (model_data == null) {
    return;
  };
  /* enable plot element: */
  var plot_container_el = plot_vars['plot_container_el'];
  plot_container_el.style.display = plot_vars['plot_container_el_display'];
  /* get wavelengths and index of 550nm: */
  var wavelengths = model_data['wavelengths']
  var index_550 = wavelengths.indexOf(550)

  /* -- time series plot: -- */

  /* time series variables: */
  var saod_ts_title = plot_vars['saod_ts_title'];
  var saod_ts_x_title = plot_vars['saod_ts_x_title'];
  var saod_ts_y_title = plot_vars['saod_ts_y_title'];
  var saod_ts_el = plot_vars['saod_ts_el'];
  /* get time series data: */
  var saod_ts_scatter_x = model_data['time_years'];
  var saod_ts_scatter_xlabel = model_data['time_dates'];
  var saod_ts_scatter_y = [];
  var saod_ts_hover = [];
  /* loop through wavelengths: */
  for (var i = 0; i < wavelengths.length; i++) {
    /* get saod time series values: */
    saod_ts_scatter_y[i] = model_data['saod_ts'][i];
    /* create hover text for time series plot: */
    saod_ts_hover[i] = [];
    for (var j = 0; j < saod_ts_scatter_x.length; j++) {
      /* date and saod values for this point: */
      var hover_date = saod_ts_scatter_xlabel[j];
      var hover_saod = saod_ts_scatter_y[i][j];
      saod_ts_hover[i][j] = 'Date: ' + hover_date + '<br>' + 'SAOD at ' +
                            wavelengths[i] + 'nm: ' + hover_saod;
    };
  };
  /* create time series plots ... plot data in order of plotting: */
  var saod_ts_data = [];
  /* loop through wavelengths: */
  for (var i = 0; i < wavelengths.length; i++) {
    /* wavelength for this plot: */
    var my_wavelength = wavelengths[i];
    /* name for this plot: */
    var my_name = my_wavelength + 'nm';
    /* create time series scatter plot and append to array of plots: */
    saod_ts_data.push({
      'type': 'scatter',
      'name': my_name,
      'x': saod_ts_scatter_x,
      'y': saod_ts_scatter_y[i],
      'mode': 'lines',
      'marker': {
        'color': plot_vars['saod_ts_colors'][i]
      },
      'hoverinfo': 'text',
      'hovertext': saod_ts_hover[i]
    });
  };
  /* saod time series layout: */
  var saod_ts_layout = {
    'title': {
      'text': saod_ts_title,
    },
    'xaxis': {
      'title': saod_ts_x_title,
      'zeroline': false
    },
    'yaxis': {
      'title': saod_ts_y_title,
      'zeroline': false
    },
    'legend': {
      'x': 1,
      'y': 1,
      'xanchor': 'right'
    },
    'hovermode': 'closest'
  };
  /* saod time series config: */
  var saod_ts_conf = {
    'showLink': false,
    'linkText': '',
    'displaylogo': false,
    'modeBarButtonsToRemove': [
      'autoScale2d',
      'lasso2d',
      'toggleSpikelines',
      'select2d'
    ],
    'responsive': true
  };
  /* if plot does not exist: */
  if (plot_vars['saod_ts_plot'] == null) {
    /* create the plot and store in plot_vars: */
    plot_vars['saod_ts_plot'] = Plotly.newPlot(
      saod_ts_el, saod_ts_data, saod_ts_layout, saod_ts_conf
    );
  } else {
    /* update the plot: */
    Plotly.react(
      saod_ts_el, saod_ts_data, saod_ts_layout, saod_ts_conf
    );
  };

  /* -- contour plot: -- */

  /* contour plot variables: */
  var saod_contour_x = model_data['time_years'];
  var saod_contour_xlabel = model_data['time_dates'];
  var saod_contour_y = model_data['lat'];
  var saod_contour_z = model_data['saod'][index_550];
  var saod_contour_z_min = 999999;
  var saod_contour_z_max = -999999;
  var saod_contour_colorscale = plot_vars['saod_contour_colorscale'];
  var saod_contour_cb_title = plot_vars['saod_contour_cb_title'];
  var saod_contour_title = plot_vars['saod_contour_title'];
  var saod_contour_x_title = plot_vars['saod_contour_x_title'];
  var saod_contour_y_title =  plot_vars['saod_contour_y_title'];
  var saod_contour_el = plot_vars['saod_contour_el'];
  /* create hover text for contour plot: */
  var saod_contour_hover = [];
  for (var i = 0; i < saod_contour_y.length; i++) {
    saod_contour_hover[i] = [];
    for (var j = 0; j < saod_contour_x.length; j++) {
      /* values for this point: */
      var hover_date = saod_contour_xlabel[j];
      var hover_lat = saod_contour_y[i];
      var hover_saod = saod_contour_z[i][j];
      /* update min and max values: */
      saod_contour_z_min = Math.min(saod_contour_z_min, hover_saod);
      saod_contour_z_max = Math.max(saod_contour_z_max, hover_saod);
      /* add to hover text: */
      saod_contour_hover[i][j] = 'Date: ' + hover_date + '<br>' +
                                 'Latitude: ' + hover_lat + '<br>' +
                                 'SAOD at 550nm: ' + hover_saod;
    };
  };
  /* color bar: */
  var saod_contour_cb = {
    'title': {
      'text': saod_contour_cb_title,
      'side': 'right'
    },
    'thickness': 20,
    'len': 0.9
  };
  /* saod contour plot: */
  var saod_contour = {
    'type': 'contour',
    'name': '550nm',
    'x': saod_contour_x,
    'y': saod_contour_y,
    'z': saod_contour_z,
    'zmin': saod_contour_z_min,
    'zmax': saod_contour_z_max,
    'colorscale': saod_contour_colorscale,
    'colorbar': saod_contour_cb,
    'hoverinfo': 'text',
    'text': saod_contour_hover
  };
  /* plot data in order of plotting: */
  var saod_contour_data = [saod_contour];
  /* saod contour plot update: */
  var saod_contour_update = {
    'x': [saod_contour_x],
    'y': [saod_contour_y],
    'z': [saod_contour_z],
    'zmin': [saod_contour_z_min],
    'zmax': [saod_contour_z_max],
    'colorbar': [saod_contour_cb],
    'text': [saod_contour_hover]
  };
  /* saod contour plot layout: */
  var saod_contour_layout = {
    'title': {
      'text': saod_contour_title,
    },
    'xaxis': {
      'title': saod_contour_x_title,
      'zeroline': false
    },
    'yaxis': {
      'title': saod_contour_y_title,
      'zeroline': false,
      'tickvals': [-80, -40, 0, 40, 80]
    },
    'hovermode': 'closest'
  };
  /* saod contour plot config: */
  var saod_contour_conf = {
    'showLink': false,
    'linkText': '',
    'displaylogo': false,
    'modeBarButtonsToRemove': [
      'autoScale2d',
      'lasso2d',
      'toggleSpikelines',
      'select2d'
    ],
    'responsive': true
  };
  /* if plot does not exist: */
  if (plot_vars['saod_contour_plot'] == null) {
    /* create the plot and store in plot_vars: */
    plot_vars['saod_contour_plot'] = Plotly.newPlot(
      saod_contour_el, saod_contour_data, saod_contour_layout,
      saod_contour_conf
    );
  } else {
    /* update the plot: */
    Plotly.update(
      saod_contour_el, saod_contour_update, saod_contour_layout
    );
  };

  /* -- fair rf time series plot: -- */

  /* time series variables: */
  var fair_rf_ts_title = plot_vars['fair_rf_ts_title'];
  var fair_rf_ts_x_title = plot_vars['fair_rf_ts_x_title'];
  var fair_rf_ts_y_title = plot_vars['fair_rf_ts_y_title'];
  var fair_rf_ts_el = plot_vars['fair_rf_ts_el'];
  /* with eruption: */
  var fair_rf_ts_scatter_x = model_data['fair_years'];
  var fair_rf_ts_scatter_y = model_data['fair_rf'];
  /* with eruption: */
  var fair_rf_wo_ts_scatter_x = model_data['fair_years'];
  var fair_rf_wo_ts_scatter_y = model_data['fair_rf_wo'];
  /* create hover text for time series plot: */
  var fair_rf_ts_hover = [];
  var fair_rf_wo_ts_hover = [];
  for (var i = 0; i < fair_rf_ts_scatter_x.length; i++) {
    /* year and rf values for this point: */
    var hover_year_rf = fair_rf_ts_scatter_x[i];
    var hover_rf = fair_rf_ts_scatter_y[i];
    var hover_year_rf_wo = fair_rf_wo_ts_scatter_x[i];
    var hover_rf_wo = fair_rf_wo_ts_scatter_y[i];
    /* add to hover text: */
    fair_rf_ts_hover[i] = 'Year: ' + hover_year_rf + '<br>' +
                          'Radiative forcing: ' + hover_rf + ' W/m⁻²';
    fair_rf_wo_ts_hover[i] = 'Year: ' + hover_year_rf_wo + '<br>' +
                             'Radiative forcing: ' + hover_rf_wo + ' W/m⁻²';
  };
  /* fair rf time series plot ... : */
  var fair_rf_ts_scatter = {
    'type': 'scatter',
    'name': 'With eruption',
    'x': fair_rf_ts_scatter_x,
    'y': fair_rf_ts_scatter_y,
    'mode': 'lines',
    'marker': {
      'color': plot_vars['fair_rf_ts_col']
    },
    'hoverinfo': 'text',
    'hovertext': fair_rf_ts_hover
  };
  /* without eruption: */
  var fair_rf_wo_ts_scatter = {
    'type': 'scatter',
    'name': 'Without eruption',
    'x': fair_rf_wo_ts_scatter_x,
    'y': fair_rf_wo_ts_scatter_y,
    'mode': 'lines',
    'marker': {
      'color': plot_vars['fair_rf_wo_ts_col']
    },
    'hoverinfo': 'text',
    'hovertext': fair_rf_wo_ts_hover
  };
  /* plot data in order of plotting: */
  var fair_rf_ts_data = [
    fair_rf_ts_scatter, fair_rf_wo_ts_scatter
  ];
  /* fair rf time series update: */
  var fair_rf_ts_update = {
    'x': [
      fair_rf_ts_scatter_x, fair_rf_wo_ts_scatter_x
    ],
    'y': [
      fair_rf_ts_scatter_y, fair_rf_wo_ts_scatter_y
    ],
    'hovertext': [fair_rf_ts_hover, fair_rf_wo_ts_hover]
  };
  /* fair rf time series layout: */
  var fair_rf_ts_layout = {
    'title': {
      'text': fair_rf_ts_title,
    },
    'xaxis': {
      'title': fair_rf_ts_x_title,
      'zeroline': false
    },
    'yaxis': {
      'title': fair_rf_ts_y_title,
      'zeroline': false
    },
    'legend': {
      'x': 0,
      'y': 0,
      'xanchor': 'left',
      'yanchor': 'bottom'
    },
    'hovermode': 'closest'
  };
  /* fair rf time series config: */
  var fair_rf_ts_conf = {
    'showLink': false,
    'linkText': '',
    'displaylogo': false,
    'modeBarButtonsToRemove': [
      'autoScale2d',
      'lasso2d',
      'toggleSpikelines',
      'select2d'
    ],
    'responsive': true
  };
  /* if plot does not exist: */
  if (plot_vars['fair_rf_ts_plot'] == null) {
    /* create the plot and store in plot_vars: */
    plot_vars['fair_rf_ts_plot'] = Plotly.newPlot(
      fair_rf_ts_el, fair_rf_ts_data, fair_rf_ts_layout, fair_rf_ts_conf
    );
  } else {
    /* update the plot: */
    Plotly.update(
      fair_rf_ts_el, fair_rf_ts_update, fair_rf_ts_layout
    );
  };

  /* -- fair temp time series plot: -- */

  /* time series variables: */
  var fair_temp_ts_title = plot_vars['fair_temp_ts_title'];
  var fair_temp_ts_x_title = plot_vars['fair_temp_ts_x_title'];
  var fair_temp_ts_y_title = plot_vars['fair_temp_ts_y_title'];
  var fair_temp_ts_el = plot_vars['fair_temp_ts_el'];
  /* with eruption: */
  var fair_temp_ts_scatter_x = model_data['fair_years'];
  var fair_temp_ts_scatter_y = model_data['fair_temp'];
  /* with eruption: */
  var fair_temp_wo_ts_scatter_x = model_data['fair_years'];
  var fair_temp_wo_ts_scatter_y = model_data['fair_temp_wo'];
  /* create hover text for time series plot: */
  var fair_temp_ts_hover = [];
  var fair_temp_wo_ts_hover = [];
  for (var i = 0; i < fair_temp_ts_scatter_x.length; i++) {
    /* year and temp values for this point: */
    var hover_year_temp = fair_temp_ts_scatter_x[i];
    var hover_temp = fair_temp_ts_scatter_y[i];
    var hover_year_temp_wo = fair_temp_wo_ts_scatter_x[i];
    var hover_temp_wo = fair_temp_wo_ts_scatter_y[i];
    /* add to hover text: */
    fair_temp_ts_hover[i] = 'Year: ' + hover_year_temp + '<br>' +
                            'Temperature anomaly: ' + hover_temp + ' K';
    fair_temp_wo_ts_hover[i] = 'Year: ' + hover_year_temp_wo + '<br>' +
                               'Temperature anomaly: ' + hover_temp_wo + ' K';
  };
  /* fair temp time series plot ... : */
  var fair_temp_ts_scatter = {
    'type': 'scatter',
    'name': 'With eruption',
    'x': fair_temp_ts_scatter_x,
    'y': fair_temp_ts_scatter_y,
    'mode': 'lines',
    'marker': {
      'color': plot_vars['fair_temp_ts_col']
    },
    'hoverinfo': 'text',
    'hovertext': fair_temp_ts_hover
  };
  /* without eruption: */
  var fair_temp_wo_ts_scatter = {
    'type': 'scatter',
    'name': 'Without eruption',
    'x': fair_temp_wo_ts_scatter_x,
    'y': fair_temp_wo_ts_scatter_y,
    'mode': 'lines',
    'marker': {
      'color': plot_vars['fair_temp_wo_ts_col']
    },
    'hoverinfo': 'text',
    'hovertext': fair_temp_wo_ts_hover
  };
  /* plot data in order of plotting: */
  var fair_temp_ts_data = [
    fair_temp_ts_scatter, fair_temp_wo_ts_scatter
  ];
  /* fair temp time series update: */
  var fair_temp_ts_update = {
    'x': [
      fair_temp_ts_scatter_x, fair_temp_wo_ts_scatter_x
    ],
    'y': [
      fair_temp_ts_scatter_y, fair_temp_wo_ts_scatter_y
    ],
    'hovertext': [fair_temp_ts_hover, fair_temp_wo_ts_hover]
  };
  /* fair temp time series layout: */
  var fair_temp_ts_layout = {
    'title': {
      'text': fair_temp_ts_title,
    },
    'xaxis': {
      'title': fair_temp_ts_x_title,
      'zeroline': false
    },
    'yaxis': {
      'title': fair_temp_ts_y_title,
      'zeroline': false
    },
    'legend': {
      'x': 0,
      'y': 0,
      'xanchor': 'left',
      'yanchor': 'bottom'
    },
    'hovermode': 'closest'
  };
  /* fair temp time series config: */
  var fair_temp_ts_conf = {
    'showLink': false,
    'linkText': '',
    'displaylogo': false,
    'modeBarButtonsToRemove': [
      'autoScale2d',
      'lasso2d',
      'toggleSpikelines',
      'select2d'
    ],
    'responsive': true
  };
  /* if plot does not exist: */
  if (plot_vars['fair_temp_ts_plot'] == null) {
    /* create the plot and store in plot_vars: */
    plot_vars['fair_temp_ts_plot'] = Plotly.newPlot(
      fair_temp_ts_el, fair_temp_ts_data, fair_temp_ts_layout,
      fair_temp_ts_conf
    );
  } else {
    /* update the plot: */
    Plotly.update(
      fair_temp_ts_el, fair_temp_ts_update, fair_temp_ts_layout
    );
  };
};

/* function to display some model output stats: */
function display_stats() {
  /* time series stats ... get wavelengths and dates: */
  var wavelengths = model_data['wavelengths'];
  var time_dates = model_data['time_dates'];
  /* wipe out any html content first: */
  var stats_a_el = stats_els['stats_a_div'];
  stats_a_el.innerHTML = '';
  /* loop through wavelengths: */
  for (var i = 0; i < wavelengths.length; i++) {
    /* this wavelength: */
    var my_wavelength = wavelengths[i];
    /* this time series: */
    var saod_ts = model_data['saod_ts'][i];
    /* get peak value: */
    var peak_value = Math.max.apply(Math, saod_ts);
    /* get peak date: */
    var peak_index =  saod_ts.indexOf(peak_value);
    var peak_date = time_dates[peak_index].substring(0, 7);
    /* add div for the stat: */
    stats_a_el.innerHTML += '<div class="model_stats">' +
                            '<label class="model_stats_label">' +
                            'Peak monthly SAOD at ' + my_wavelength + 'nm: ' +
                            '</label>' +
                            '<span class="model_stats_value">' +
                            peak_value + ' (' + peak_date + ')' +
			    '</span>' +
                            '</div>';
  };
  /* additional variables of interest: */
  var rf_ts = model_data['rf_ts'];
  var fair_temp = model_data['fair_temp'];
  var fair_temp_wo = model_data['fair_temp_wo'];
  var fair_year = model_data['fair_years'];
  /* get the peak rf value: */
  var rf_peak_value = Math.min.apply(Math, rf_ts);
  var rf_peak_index = rf_ts.indexOf(rf_peak_value);
  var rf_peak_date = time_dates[rf_peak_index].substring(0, 7);
  /*
   * get peak temperature anomaly value / where there is the max diff between
   * with and without eruption:
   */
  var fair_temp_max_diff = -999999;
  var fair_temp_peak_value = null;
  var fair_temp_peak_index = null;
  for (var i = 1; i < fair_temp.length; i++) {
    var my_diff = Math.abs(fair_temp_wo[i] - fair_temp[i]);
    if (my_diff > fair_temp_max_diff) {
      fair_temp_max_diff = my_diff;
      fair_temp_peak_value = fair_temp[i] - fair_temp_wo[i];
      fair_temp_peak_index = i;
    };
  };
  var fair_temp_peak_value = fair_temp_peak_value.toFixed(6);
  var fair_temp_peak_date = fair_year[fair_temp_peak_index];
  /* update html elements: */
  stats_els['rf_peak_label'].innerHTML = 'Peak monthly radiative forcing:';
  stats_els['rf_peak_value'].innerHTML = rf_peak_value +
                                         ' W/m⁻² (' + rf_peak_date + ')';
  stats_els['fair_temp_peak_label'].innerHTML = 'Peak annual temperature anomaly:';
  stats_els['fair_temp_peak_value'].innerHTML = fair_temp_peak_value +
                                         ' K (' + fair_temp_peak_date + ')';
};

/* run the model by posting parameters: */
function __run_model(model_params) {
  /* init result variable: */
  var model_result;
  /* run button element: */
  var input_run_button = input_els['run_button'];
  input_els['run_button_display'] = input_run_button.style.display;
  /* model spinner element: */
  var model_spinner = plot_vars['model_spinner'];
  /* disable run button: */
  input_run_button.setAttribute('disabled', true);
  input_run_button.style.display = 'none';
  /* enable spinner: */
  model_spinner.style.display = 'inline';
  /* build request parameters: */
  var req_params = 'wavelengths=[' + model_params['wavelengths'] + ']&' +
                   'lat=' + model_params['lat'] + '&' +
                   'year=' + model_params['year'] + '&' +
                   'month=' + model_params['month'] + '&' +
                   'so2_mass=' + model_params['so2_mass'] + '&' +
                   'so2_height=' + model_params['so2_height'] + '&' +
                   'tropo_height=' + model_params['tropo_height'] + '&' +
                   'so2_timescale=' + model_params['so2_timescale'] + '&' +
                   'rad_eff=' + model_params['rad_eff'] + '&' +
                   'nc=' + model_params['nc'];
  /* request error function: */
  function model_req_error() {
    console.log('* model error');
    /* disable model spinner element: */
    var model_spinner = plot_vars['model_spinner'];
    model_spinner.style.display = 'none';
    /* run button element: */
    var input_run_button = input_els['run_button'];
    /* enable run button: */
    input_run_button.removeAttribute('disabled');
    input_run_button.style.display = input_els['run_button_display'];
    input_run_button.blur();
  };
  /* create new request: */
  var model_req = new XMLHttpRequest();
  model_req.responseType = 'json';
  model_req.open('POST', model_url, true);
  model_req.setRequestHeader(
    'Content-type', 'application/x-www-form-urlencoded'
  );
  /* on request load: */
  model_req.onload = function() {
    /* if not successful: */
    if (model_req.status != 200) {
      model_req_error();
    } else {
      /* model results: */
      model_result = model_req.response;
      console.log('* model run result:');
      console.log(model_result['status'] + ': ' + model_result['message']);
      /* if model succeeded: */
      if (model_result['status'] == 0) {
        /* store model data: */
        model_data = model_result['data'];
        /* disable status: */
        model_spinner.style.display = 'none';
        /* plot the data: */
        plot_data();
        /* display stats: */
        display_stats();
        /* enable run button: */
        input_run_button.removeAttribute('disabled');
        input_run_button.style.display = input_els['run_button_display'];
        input_run_button.blur();
      /* else, handle error: */
      } else {
        model_req_error();
      };
    };
    /* if request fails: */
    model_req.onerror = function() {
      model_req_error();
    };
  };
  /* send the request: */
  console.log('* model pameters:');
  console.log(model_params);
  model_req.send(req_params);
};

/* model running function: */
function run_model() {
  /* validate input / get model parameters: */
  validate_text_input();
  validate_select_input();
  /* if parameters are o.k.: */
  if (model_params_ok == true) {
    /* run the model by posting parameters: */
    var result = __run_model(model_params);
  };
};

/* function to get data as csv: */
async function get_csv_data() {
  /* model time series first ... get variables: */
  var wavelengths = model_data['wavelengths'];
  var time_dates = model_data['time_dates'];
  var saod_ts = model_data['saod_ts'];
  var rf_ts = model_data['rf_ts'];
  /* create zip write object: */
  const zip_writer = new zip.ZipWriter(new zip.Data64URIWriter("application/zip"));
  /* csv header line: */
  var csv_data = 'date,';
  for (var i = 0; i < wavelengths.length; i++) {
    csv_data += 'saod_' + wavelengths[i] + 'nm,';
  };
  csv_data += 'radiative_forcing\r\n';
  /* loop through values: */
  for (var i = 0; i < time_dates.length; i++) {
    /* add line to csv: */
    csv_data += time_dates[i] + ',';
    for (var j = 0; j < wavelengths.length; j++) {
      csv_data += saod_ts[j][i] + ',';
    };
    csv_data += rf_ts[i] + '\r\n';
  };
  /* add csv data to zip file: */
  await zip_writer.add('saod_time_series.csv', new zip.TextReader(csv_data));

  /* model 2d saod at ... get variables: */
  var lat = model_data['lat'];
  var saod = model_data['saod'];
  /* csv header line: */
  csv_data = 'date,lat';
  for (var i = 0; i < wavelengths.length; i++) {
    csv_data += ',saod_' + wavelengths[i] + 'nm';
  };
  csv_data += '\r\n';
  /* loop through values: */
  for (var i = 0; i < lat.length; i++) {
    for (var j = 0; j < time_dates.length; j++) {
      /* add line to csv: */
      csv_data += time_dates[j] + ',' +
                  lat[i];
      for (var k = 0; k < wavelengths.length; k++) {
        csv_data += ',' + saod[k][i][j];
      };
      csv_data += '\r\n';
    };
  };
  /* add csv data to zip file: */
  await zip_writer.add('saod.csv', new zip.TextReader(csv_data));
  /* fair time series ... get variables: */
  var fair_years = model_data['fair_years'];
  var fair_rf = model_data['fair_rf'];
  var fair_rf_wo = model_data['fair_rf_wo'];
  var fair_temp = model_data['fair_temp'];
  var fair_temp_wo = model_data['fair_temp_wo'];
  /* csv header line: */
  csv_data = 'year,radiative_forcing,radiative_forcing_with_eruption,temperature_anomaly,temperature_anomaly_with_eruption\r\n';
  /* loop through values: */
  for (var i = 0; i < fair_years.length; i++) {
    /* add line to csv: */
    csv_data += fair_years[i] + ',' +
                fair_rf_wo[i] + ',' +
                fair_rf[i] + ',' +
                fair_temp_wo[i] + ',' +
                fair_temp[i] + '\r\n';
  };
  /* add csv data to zip file: */
  await zip_writer.add('fair_time_series.csv', new zip.TextReader(csv_data));
  /* close zip file and get encoded data uri: */
  const data_uri = await zip_writer.close();
  /* name for zip file: */
  var zip_name = 'model_data.zip';
  /* create a temporary link element: */
  var zip_link = document.createElement("a");
  zip_link.setAttribute("href", data_uri);
  zip_link.setAttribute("download", zip_name);
  zip_link.style.visibility = 'hidden';
  /* add link to document, click to init download, then remove: */
  document.body.appendChild(zip_link);
  zip_link.click();
  document.body.removeChild(zip_link);
};

/* function to get data as netcdf: */
async function get_nc_data() {
  /* get base64 encdoded netcdf data: */
  var nc_data = encodeURI(
    'data:application/x-netcdf;base64,' +  model_data['nc']
  );
  /* name for csv file: */
  var nc_name = 'model_data.nc';
  /* create a temporary link element: */
  var nc_link = document.createElement("a");
  nc_link.setAttribute("href", nc_data);
  nc_link.setAttribute("download", nc_name);
  nc_link.style.visibility = 'hidden';
  /* add link to document, click to init download, then remove: */
  document.body.appendChild(nc_link);
  nc_link.click();
  document.body.removeChild(nc_link);
};

/* --- --- */

/* on page load ... : */
window.addEventListener('load', function() {
  /* configure zip.js: */
  zip.configure({
    useWebWorkers: true,
    maxWorkers: 2,
    workerScripts: {
      deflate: [static_prefix + 'js/z-worker-fflate.js',
                static_prefix + 'js/fflate.min.js'],
    }
  });
  /* add listeners to various elements: */
  add_listeners();
  /* hide some elements ... : */
  hide_elements();
});
