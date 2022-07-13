# -*- coding: utf-8 -*-

"""
Volcanic forcing and climate response tool
"""

# --- imports

# std lib imports:
import json
import os

# third party imports:
from flask import Flask, render_template, request

# local imports:
from model import run_model

# --- global variables

# define flask application:
app = Flask(__name__)
# define site root:
SITE_ROOT = os.path.realpath(app.root_path)
# define path to eva_h directory:
EVA_H_DIR = os.sep.join([SITE_ROOT, 'eva_h'])
# define path to config and read:
CONFIG_FILE = os.sep.join([SITE_ROOT, 'config.json'])
with open(CONFIG_FILE, 'r', encoding='utf-8') as CONFIG_JSON:
    APP_CONFIG = json.load(CONFIG_JSON)
# define flask app secret key:
app.secret_key = APP_CONFIG['secret_key']

# ---

# home:
@app.route('/', methods=['GET'])
def render_home():
    """
    Render home page
    """
    # return rendered home page:
    return render_template(
        'home.html.j2', current_page='home', header_img=True,
    )

# about:
@app.route('/about', methods=["GET"])
def render_contact():
    """
    Render contact page
    """
    # return rendered contact page:
    return render_template(
        'about.html.j2', current_page='about', header_img=True
    )

# model:
@app.route('/model', methods=['POST'])
def model():
    """
    Run the model
    """
    # get POST data:
    request_params = request.form
    # run the model:
    result = run_model(EVA_H_DIR, request_params)
    # return the result:
    return result

# error:
@app.errorhandler(Exception)
def handle_exception(error):
    """
    Handle errors
    """
    return render_template(
        'error.html.j2', current_page='error', error=error.description
    ), error.code

if __name__ == '__main__':
    app.run(debug=True)
