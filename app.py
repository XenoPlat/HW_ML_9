import h2o
from flask import Flask, request, jsonify

from process_data import process_input

import logging
import traceback
from logging.handlers import RotatingFileHandler
from time import strftime, time

app = Flask(__name__)

h2o.init()
model_glm_poisson = h2o.load_model('GLM_model_python_1')
model_glm_gamma = h2o.load_model('GLM_model_python_2')

handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=5)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

@app.route("/")
def index():
    return "API 4 predict srvc"

@app.route("/predict", methods=['POST'])
def predict():
    json_input = request.json

    current_datatime = strftime('[%Y-%b-%d %H:%M:%S]')
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    logger.info(f'{current_datatime} request from {ip_address}: {request.json}')
    start_prediction = time()

    ID = json_input['ID']
    hf = process_input(json_input)

    prediction_Poisson = model_glm_poisson.predict(hf)
    value_Poisson = prediction_Poisson.as_data_frame()['predict'][0]

    prediction_Gamma = model_glm_gamma.predict(hf)
    value_Gamma = prediction_Gamma.as_data_frame()['predict'][0]

    value_BurningCost = value_Poisson * value_Gamma

    result = {
        'ID': ID,
        'value_Poisson': value_Poisson,
        'value_Gamma': value_Gamma,
        'value_BurningCost': value_BurningCost
    }

    end_prediction = time()
    duration = round(end_prediction - start_prediction, 6)
    current_datatime = strftime('[%Y-%b-%d %H:%M:%S]')
    logger.info(f'{current_datatime} predicted for {duration} msec: {result}\n')

    return jsonify(result)

@app.errorhandler(Exception)
def exceptions(e):
    current_datatime = strftime('[%Y-%b-%d %H:%M:%S]')
    error_message = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                 current_datatime,
                 request.remote_addr,
                 request.method,
                 request.scheme,
                 request.full_path,
                 error_message)
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(debug=True)