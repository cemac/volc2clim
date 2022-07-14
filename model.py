# -*- coding: utf-8 -*-

"""
Code to run the EVA_H and FAIR models
"""

# --- imports

# std lib imports:
import datetime
import sys

# third party imports:
from fair.RCPs import rcp45
from fair.ancil import cmip5_annex2_forcing as ar5
from fair.forward import fair_scm
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
    Check supplied parameters

    :param request_params: POST supplied parameters
    """
    # expected parameters:
    params = [
        {'name': 'lat', 'type': float},
        {'name': 'year', 'type': int},
        {'name': 'month', 'type': int},
        {'name': 'so2_mass', 'type': float},
        {'name': 'so2_height', 'type': float},
        {'name': 'tropo_height', 'type': float},
        {'name': 'so2_timescale', 'type': float},
        {'name': 'scale_factor', 'type': float}
    ]
    # init output dict:
    user_params = {}
    # loop through expected parameters and try to get values:
    for param in params:
        param_name = param['name']
        param_type = param['type']
        try:
            user_params[param_name] = param_type(request_params[param_name])
        # return False on failure:
        except:
            return False, {}
    # return the parameters:
    return True, user_params

def __run_model(eva_h_dir, user_params):
    """
    Main model running function

    :param eva_h_dir: Directory containing EVA_H data files
    :param user_params: User supplied parameters
    """
    # convert parameters to numpy arrays:
    for i in user_params:
        user_params[i] = np.array([user_params[i]], dtype=float)
    # init the model parameters:
    model_params = ModelParams()
    # adjust so2 timescale to user provided value:
    model_params.tauprod = np.ones(8) * user_params['so2_timescale']
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
    wl_req = np.array([0.380, 0.550, 1.020])
    # run the post processing:
    gmsaod, saod, reff, ext, ssa, asy, lat, alt = postproc(
        eva_h_dir, so4_mass, model_params, model_params.mstar,
        model_params.R_reff, wl_req
    )
    # convert values for json output ..
    # model time in years to 2 decimal places:
    model_time_years = (tref / 12)
    model_time_years = np.round(model_time_years, 2).tolist()
    # time series saod 380 to 6 decimal places:
    model_saod_380_ts = np.round(gmsaod[:, 0], 6).tolist()
    # time series saod 550 to 6 decimal places:
    model_saod_550_ts = np.round(gmsaod[:, 1], 6).tolist()
    # time series saod 1020 to 6 decimal places:
    model_saod_1020_ts = np.round(gmsaod[:, 2], 6).tolist()
    # model latitude:
    model_lat = lat.tolist()
    # saod 550 to 6 decimal places:
    model_saod_550 = np.round((saod[:, :, 1]).T, 6).tolist()
    # radiative forcing is model_saod_550_ts multiplied by negative scaling
    # factor:
    model_rf = user_params['scale_factor'] * model_saod_550_ts
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
    conc_a, forcing_a, temp_a = fair_scm(
        emissions=rcp45.Emissions.emissions,
        F_volcanic=ar5_volcanic
    )
    # update volcanic forcing values with those from eva_h:
    for i, model_year in enumerate(model_years):
        ar5_volcanic[rcp45.Emissions.year == model_year] += model_rf_means[i]
    # run fair with eva_h updates:
    conc_b, forcing_b, temp_b = fair_scm(
        emissions=rcp45.Emissions.emissions,
        F_volcanic=ar5_volcanic
    )
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
    # data dict for output:
    model_data = {
        'time_years': model_time_years,
        'time_dates': model_time_dates,
        'lat': model_lat,
        'saod_380_ts': model_saod_380_ts,
        'saod_550_ts': model_saod_550_ts,
        'saod_1020_ts': model_saod_1020_ts,
        'saod_550': model_saod_550,
        'rf_ts': model_rf,
        'fair_years': fair_years,
        'fair_rf_wo': fair_rf_wo,
        'fair_rf': fair_rf,
        'fair_temp_wo': fair_temp_wo,
        'fair_temp': fair_temp
    }
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
    status, user_params = check_params(request_params)
    # if that failed ... :
    if not status:
        # updata result dict:
        result['status'] = 1
        result['message'] = 'invalid parameters'
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
