# -*- coding: utf-8 -*-

"""
Code to run the EVA_H and FAIR models
"""

# --- imports

# std lib imports:
import base64 as b64
import datetime
import sys

# third party imports:
from fair.RCPs import rcp45
from fair.ancil import cmip5_annex2_forcing as ar5
from fair.forward import fair_scm
import netCDF4 as nc
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator

# local imports:
from eva_h.eightboxequations import eightboxequations
from eva_h.parameters import ModelParams
from eva_h.postproc import postproc
from eva_h.so2injection_8boxes import so2injection_8boxes

# --- global variables


# ---

def check_params(request_params):
    """
    Check supplied parameters, convrting values as required

    :param request_params: POST supplied parameters
    """
    # init output dict:
    user_params = {}
    # handle wavelength values first. if wavelengths parameters present:
    if 'wavelengths' in request_params.keys():
        try:
            # get requested values:
            wavelengths_in = request_params['wavelengths']
            # convert from string to list:
            wavelengths_out = [
                float(i) for i in
                wavelengths_in.lstrip('[').rstrip(']').split(',')
            ]
            # if 550 is not in the list, add it:
            if 550 not in wavelengths_out:
                wavelengths_out.append(550)
            # convert to numpy array, scale and sort the values:
            wavelengths_out = np.array(wavelengths_out) / 1000
            wavelengths_out.sort()
            # store the unique wavelength values:
            user_params['wavelengths'] = np.unique(wavelengths_out)
        except:
            err_msg = 'invalid wavelengths parameter'
            return False, {}, err_msg
    else:
        # no parameters present. use default values:
        user_params['wavelengths'] = np.array([380, 550, 1020]) / 1000
    # additional expected parameters:
    params = [
        {'name': 'lat', 'type': float},
        {'name': 'year', 'type': int},
        {'name': 'month', 'type': int},
        {'name': 'so2_mass', 'type': float},
        {'name': 'so2_height', 'type': float},
        {'name': 'tropo_height', 'type': float},
        {'name': 'aerosol_timescale', 'type': float},
        {'name': 'rad_eff', 'type': float}
    ]
    # loop through expected parameters and try to get values:
    for param in params:
        param_name = param['name']
        param_type = param['type']
        try:
            user_params[param_name] = np.array([
                param_type(request_params[param_name])
            ])
        # return False on failure:
        except:
            err_msg = 'invalid {} parameter'.format(param_name)
            return False, {}, err_msg
    # check for optional netcdf flag, presume not:
    user_params['nc'] = False
    if 'nc' in request_params.keys():
        # 1 is True, anything else is False:
        if request_params['nc'] == '1':
            user_params['nc'] = True
    # check parameter values ... so2_mass:
    for i in user_params['so2_mass']:
        if not 0 <= i <= 999999:
            err_msg = 'so2_mass parameter should not be less than 0'
            err_msg += ' or greater than 999999 ({0})'.format(i)
            return False, {}, err_msg
    # check lat:
    for i in user_params['lat']:
        if not -90 <= i <= 90:
            err_msg = 'lat parameter should not be less than -90'
            err_msg += ' or greater than 90 ({0})'.format(i)
            return False, {}, err_msg
    # check year:
    for i in user_params['year']:
        if not 1800 <= i <= 2050:
            err_msg = 'lat parameter should not be less than 1800'
            err_msg += ' or greater than 2050 ({0})'.format(i)
            return False, {}, err_msg
    # check month:
    for i in user_params['month']:
        if not 1 <= i <= 12:
            err_msg = 'month parameter should not be less than 1'
            err_msg += ' or greater than 12 ({0})'.format(i)
            return False, {}, err_msg
    # check so2_height:
    for i in user_params['so2_height']:
        if not 0 <= i <= 50:
            err_msg = 'so2_height parameter should not be less than 0'
            err_msg += ' or greater than 50 ({0})'.format(i)
            return False, {}, err_msg
    # check tropo_height:
    for i in user_params['tropo_height']:
        if not 0 <= i <= 50:
            err_msg = 'tropo_height parameter should not be less than 0'
            err_msg += ' or greater than 50 ({0})'.format(i)
            return False, {}, err_msg
    # check aerosol_timescale:
    for i in user_params['aerosol_timescale']:
        if not 0.1 <= i <= 50:
            err_msg = 'aerosol_timescale parameter should not be less than 0.1'
            err_msg += ' or greater than 50 ({0})'.format(i)
            return False, {}, err_msg
    # check rad_eff:
    for i in user_params['rad_eff']:
        if not -50 <= i <= -0.1:
            err_msg = 'rad_eff parameter should not be less than -50'
            err_msg += ' or greater than -0.1 ({0})'.format(i)
            return False, {}, err_msg
    # check wavelengths:
    for i in user_params['wavelengths']:
        if not 1 <= i * 1000 <= 5000:
            err_msg = 'wavelength parameter should not be less than 1'
            err_msg += ' or greater than 5000 ({0})'.format(round(i * 1000))
            return False, {}, err_msg
    # return the parameters:
    return True, user_params, None

def data_to_nc(model_dates, model_lats, model_alts, model_wls,
               model_ext, model_ssa, model_asy, model_saod):
    """
    Create NetCDF dataset for model data and return as base64

    :param model_dates: List of model dates as strings in format %Y-%m-%d
    :param model_lats: Numpy array of model latitudes
    :param model_alts: Numpy array of model altitudes
    :param model_wls: Numpy array of model wavelengths
    :param model_ext: Numpy array of model aerosol extinction
    :param model_ssa: Numpy array of model single scattering albedo
    :param model_ssa: Numpy array of model aerosol scattering asymmtery factor
    :param model_saod: Numpy array of model stratospheric aerosol optical depth
    """
    # create the netcdf dataset:
    nc_data = nc.Dataset(None, mode='w', memory=True, format='NETCDF4')
    # set up time units and calendar:
    nc_time_units = 'days since 1900-01-01 00:00:00'
    # convert model dates to datetimes:
    model_datetimes = [
        datetime.datetime.strptime(i, '%Y-%m-%d') for i in model_dates
    ]
    # convert datetimes to netcdf times:
    nc_time_values = nc.date2num(model_datetimes, nc_time_units)
    # create time dimension:
    nc_data.createDimension('time', len(model_datetimes))
    # create time variable:
    nc_times = nc_data.createVariable('time', 'f', ('time'))
    # store the times, long name, standard_name, units and calendar:
    nc_times[:] = nc_time_values
    nc_times.long_name = 'time'
    nc_times.standard_name = 'time'
    nc_times.calendar = 'standard'
    nc_times.units = nc_time_units
    # create latitude dimension:
    nc_data.createDimension('latitude', model_lats.size)
    # create latitude variable:
    nc_lats = nc_data.createVariable('latitude', 'f', ('latitude'))
    # store the latitudes, long name, standard_name, and units:
    nc_lats[:] = model_lats
    nc_lats.long_name = 'latitude'
    nc_lats.standard_name = 'latitude'
    nc_lats.units = 'degrees_north'
    # create altitude dimension:
    nc_data.createDimension('altitude', model_alts.size)
    # create altitude variable:
    nc_alts = nc_data.createVariable('altitude', 'f', ('altitude'))
    # store the altitudes, long name, standard_name, and units:
    nc_alts[:] = model_alts
    nc_alts.long_name = 'altitude'
    nc_alts.standard_name = 'altitude'
    nc_alts.units = 'K m'
    # create wavelength dimension:
    nc_data.createDimension('wavelength', model_wls.size)
    # create wavelength variable:
    nc_wls = nc_data.createVariable('wavelength', 'f', ('wavelength'))
    # store the wavelengths, long name, and units:
    nc_wls[:] = model_wls
    nc_wls.long_name = 'wavelength'
    nc_wls.units = 'nm'
    # create aerosol extinction variable:
    nc_ext = nc_data.createVariable(
        'ext', 'f', ('time', 'latitude', 'altitude', 'wavelength'),
        zlib=True, complevel=1
    )
    # store the extinction, long name, and units:
    nc_ext[:] = model_ext
    nc_ext.long_name = 'aerosol extinction'
    nc_ext.units = 'K m**-1'
    # create single scattering albedo variable:
    nc_ssa = nc_data.createVariable(
        'ssa', 'f', ('time', 'latitude', 'altitude', 'wavelength'),
        zlib=True, complevel=1
    )
    # store the scattering and long name:
    nc_ssa[:] = model_ssa
    nc_ssa.long_name = 'single scattering albedo'
    # create aerosol scattering asymmtery factor variable:
    nc_asy = nc_data.createVariable(
        'asy', 'f', ('time', 'latitude', 'altitude', 'wavelength'),
        zlib=True, complevel=1
    )
    # store the scattering asymmetry factor and long name:
    nc_asy[:] = model_asy
    nc_asy.long_name = 'aerosol scattering asymmtery factor'
    # create stratospheric aerosol optical depth variable:
    nc_saod = nc_data.createVariable(
        'saod', 'f', ('time', 'latitude', 'wavelength'),
        zlib=True, complevel=1
    )
    # store the stratospheric aerosol optical depth and long name:
    nc_saod[:] = model_saod
    nc_saod.long_name = 'stratospheric aerosol optical depth'
    # close the dataset:
    nc_mem = nc_data.close()
    # convert to base64:
    nc_b64 = b64.b64encode(nc_mem.tobytes()).decode()
    # return base64 encoded NetCDF:
    return nc_b64

def __run_model(eva_h_dir, user_params):
    """
    Main model running function

    :param eva_h_dir: Directory containing EVA_H data files
    :param user_params: User supplied parameters
    """
    # init the model parameters:
    model_params = ModelParams()
    # adjust aerosol timescale to user provided value:
    model_params.tauprod = np.ones(8) * user_params['aerosol_timescale']
    # calculate volcanic so2 injections:
    inmass, intime = so2injection_8boxes(
        eva_h_dir,
        model_params.h1lim,
        model_params.h2lim,
        model_params.latlim,
        user_params
    )
    # model run time in years:
    run_years = 5
    # subtract 1 from month value, so january = 0:
    user_params['month'] -= 1
    # add eruption year to months:
    user_params['month'] += (user_params['year'] * 12)
    # time span in months. run for five years, starting from lowest eruption
    # date:
    start_month = user_params['month'].min()
    tspan = [start_month, start_month + (run_years * 12)]
    # set initial conditions:
    ic = np.array([0.0126,0.0468,0.0152,0.0192,0.0359,0.0218,0.0349,0.0417])
    # init arrays for model dates:
    tref = []
    model_time_dates = []
    # create time range, where each step is the first day of each month in the
    # range:
    for i in np.arange(tspan[0], tspan[1] + 1):
        # year for this time step:
        step_yr = int(np.floor(i / 12))
        # month for this time step:
        step_month = int((i % 12) + 1)
        # datetime for this time step:
        step_dt = datetime.datetime(step_yr, step_month, 1)
        # day of year for this time step:
        step_doy = step_dt.timetuple().tm_yday - 1
        # decimal year for this time step:
        if (step_yr % 4) == 0:
            step_dy = step_yr + (step_doy / 365)
        else:
            step_dy = step_yr + (step_doy / 366)
        # date string for this time step:
        step_str = step_dt.strftime('%Y-%m-%d')
        # store the date and date string:
        tref.append(step_dy)
        model_time_dates.append(step_str)
    # convert tref to numpy array in months:
    tref = np.array(tref) * 12
    # run the model:
    sol = solve_ivp(
        eightboxequations, tspan, ic,
        args=[inmass, intime, model_params, model_params.backinj],
        rtol=1e-4, atol=1e-8
    )
    so4_mass = PchipInterpolator(sol.t, sol.y.T, axis=0)(tref)
    # list of wavelengths at which output are requested, in um:
    wavelengths = user_params['wavelengths']
    # run the post processing:
    gmsaod, saod, reff, ext, ssa, asy, lat, alt = postproc(
        eva_h_dir, so4_mass, model_params, model_params.mstar,
        model_params.R_reff, wavelengths
    )
    # convert values for json output ..
    # model time in years to 2 decimal places:
    model_time_years = (tref / 12)
    model_time_years = np.round(model_time_years, 2).tolist()
    # init list for saod values at different wavelengths:
    model_saod_ts = []
    model_saod = []
    # loop through wavelengths:
    for i in range(wavelengths.size):
        # store time series data:
        model_saod_ts.append(
            np.round(gmsaod[:, i], 6).tolist()
        )
        # store 2d time-lat data:
        model_saod.append(
             np.round((saod[:, :, i]).T, 6).tolist()
        )
    # model latitude:
    model_lat = lat.tolist()
    # radiative forcing is model_saod_ts at 550nm multiplied by negative
    # scaling factor (radiative efficiency):
    index_550 = np.where(wavelengths == 0.55)[0][0]
    model_rf = user_params['rad_eff'] * model_saod_ts[index_550]
    # get annual global mean rf values for fair. get year for each time step:
    all_model_years = np.array([
        np.floor(i) for i in model_time_years
    ], dtype=int)
    # unique years in model time period:
    model_years = np.unique(all_model_years)
    model_years.sort()
    # init list for rf means:
    model_rf_means = []
    # for each unique year:
    for model_year in model_years:
        # get mean of all values for this year:
        model_rf_means.append(
            np.nanmean(model_rf[all_model_years == model_year])
        )
    # set up volcanic forcing values for fair, using ar5 values.
    # need an array of same size as rcp45 emissions, init as -0.06 background
    # forcing value:
    ar5_volcanic = np.zeros(rcp45.Emissions.year.shape) - 0.06
    # add in values available from ar5 data where available:
    for rcp45_index, rcp45_year in enumerate(rcp45.Emissions.year):
        # look for ar5 value for this year:
        ar5_index = np.where(ar5.Forcing.year == rcp45_year)
        if ar5_index[0].size > 0:
            ar5_volcanic[rcp45_index] = ar5.Forcing.volcanic[ar5_index]
    # update 2011 -> 2015 as per Schmidt et al (2018):
    ar5_volcanic[rcp45.Emissions.year == 2011] = -0.11
    ar5_volcanic[rcp45.Emissions.year == 2012] = -0.10
    ar5_volcanic[rcp45.Emissions.year == 2013] = -0.03
    ar5_volcanic[rcp45.Emissions.year == 2014] = -0.11
    ar5_volcanic[rcp45.Emissions.year == 2015] = -0.17
    # update 2019 for raikoke guess -0.20 w m-2
    ar5_volcanic[rcp45.Emissions.year == 2019] = -0.20
    # run fair without eva_h updates:
    fair_result = fair_scm(
        emissions=rcp45.Emissions.emissions,
        F_volcanic=ar5_volcanic
    )
    forcing_a = fair_result[1]
    temp_a = fair_result[2]
    # update volcanic forcing values with those from eva_h:
    for i, model_year in enumerate(model_years):
        ar5_volcanic[rcp45.Emissions.year == model_year] += model_rf_means[i]
    # run fair with eva_h updates:
    fair_result = fair_scm(
        emissions=rcp45.Emissions.emissions,
        F_volcanic=ar5_volcanic
    )
    forcing_b = fair_result[1]
    temp_b = fair_result[2]
    # get required values for year of eruption +/-10.
    # init lists for values:
    fair_years = []
    fair_rf_wo = []
    fair_rf = []
    fair_temp_wo = []
    fair_temp = []
    # loop through years:
    for i in np.arange(model_years.min() - 10, model_years.min() + 11):
        # store the year:
        fair_years.append(int(i))
        # get the index for this year:
        fair_index = np.where(rcp45.Emissions.year == i)[0][0]
        # store required values:
        fair_rf_wo.append(forcing_a[:, 11][fair_index])
        fair_rf.append(forcing_b[:, 11][fair_index])
        fair_temp_wo.append(temp_a[fair_index])
        fair_temp.append(temp_b[fair_index])
    # round values and convert to list for json output:
    model_rf = np.round(model_rf, 6).tolist()
    fair_rf_wo = np.round(fair_rf_wo, 6).tolist()
    fair_rf = np.round(fair_rf, 6).tolist()
    fair_temp_wo = np.round(fair_temp_wo, 6).tolist()
    fair_temp = np.round(fair_temp, 6).tolist()
    # expect wavelengths * 1000 (nm) to be integers:
    model_wavelengths = np.array(wavelengths * 1000, dtype=int).tolist()
    # data dict for output:
    model_data = {
        'time_years': model_time_years,
        'time_dates': model_time_dates,
        'lat': model_lat,
        'wavelengths': model_wavelengths,
        'saod_ts': model_saod_ts,
        'saod': model_saod,
        'rf_ts': model_rf,
        'fair_years': fair_years,
        'fair_rf_wo': fair_rf_wo,
        'fair_rf': fair_rf,
        'fair_temp_wo': fair_temp_wo,
        'fair_temp': fair_temp
    }
    # if netcdf data has been requested:
    if user_params['nc']:
        model_data['nc'] = data_to_nc(
            model_time_dates, lat, alt, wavelengths * 1000,
            ext, ssa, asy, saod
        )
    else:
        model_data['nc'] = ''
    # return the data:
    return model_data

def run_model(eva_h_dir, request_params):
    """
    Wrapper function for running model

    :param eva_h_dir: Directory containing EVA_H data files
    :param request_params: POST supplied parameters
    """
    # init result dict:
    result = {
        'status': -1,
        'message': '',
        'data': {}
    }
    # check user parameters:
    status, user_params, err_msg = check_params(request_params)
    # if that failed ... :
    if not status:
        # updata result dict:
        result['status'] = 1
        result['message'] = err_msg
        # return the result:
        return result
    # try to run the model:
    try:
        model_data = __run_model(eva_h_dir, user_params)
        result['status'] = 0
        result['message'] = 'model run suceeded'
        result['data'] = model_data
    # if that fails:
    except Exception as err_msg:
        sys.stderr.write('[{0}] [ERROR] {1}\n'.format(
            datetime.datetime.now(), err_msg
        ))
        result['status'] = 1
        result['message'] = 'model run failed'
    # return the result:
    return result
