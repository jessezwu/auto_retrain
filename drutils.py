import datarobot as dr
import json
import requests
import sys

def get_parent_model(model):
    """Get parent model if one exists"""
    try:
        parent_id = dr.FrozenModel.get(model.project_id, model.id).parent_model_id
        parent = dr.Model.get(model.project_id, parent_id)
        return parent
    except:
        return model

def get_default_pred_server_info():
    """Get details for default prediction server"""
    try:
        prediction_server = dr.PredictionServer.list()[0]
        pred_key = prediction_server.datarobot_key
        pred_endpoint = prediction_server.url
        return (pred_endpoint, pred_key)
    except:
        raise Exception("No prediction server found")
    
 
class DataRobotPredictionError(Exception):
    """Raised if there are issues getting predictions from DataRobot"""
 
 
def make_timeseries_prediction(data, url, deployment_id, token, key, forecast_point=None):
    """
    Make predictions on data provided using DataRobot deployment_id provided.
    See docs for details:
         https://app.datarobot.com/docs/users-guide/predictions/api/new-prediction-api.html
 
    Parameters
    ----------
    data : str
        Feature1,Feature2
        numeric_value,string
    deployment_id : str
        The ID of the deployment to make predictions with.
    forecast_point : str, optional
        The as of timestamp in ISO format
 
    Returns
    -------
    Response schema:
        https://app.datarobot.com/docs/users-guide/predictions/api/new-prediction-api.html#response-schema
 
    Raises
    ------
    DataRobotPredictionError if there are issues getting predictions from DataRobot
    """
    # Set HTTP headers. The charset should match the contents of the file.
    headers = {'Content-Type': 'text/plain; charset=UTF-8', 'datarobot-key': key, 'Authorization': 'Token {}'.format(token)}
    url = '{url}/predApi/v1.0/deployments/{deployment_id}/timeSeriesPredictions'.format(url=url, deployment_id=deployment_id)
    params = {'forecastPoint': forecast_point}
    # Make API request for predictions
    predictions_response = requests.post(
        url, data=data, headers=headers, params=params)
    _raise_dataroboterror_for_status(predictions_response)
    # Return a Python dict following the schema in the documentation
    return predictions_response.json()
 
 
def _raise_dataroboterror_for_status(response):
    """Raise DataRobotPredictionError if the request fails along with the response returned"""
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        err_msg = '{code} Error: {msg}'.format(
            code=response.status_code, msg=response.text)
        raise DataRobotPredictionError(err_msg)
 
 
def main(filename, deployment_id, forecast_point):
    """
    Return an exit code on script completion or error. Codes > 0 are errors to the shell.
    Also useful as a usage demonstration of
    `make_datarobot_deployment_predictions(data, deployment_id)`
    """
    if not filename:
        print(
            'Input file is required argument. \n'
            'Usage: python datarobot-predict.py '
            '<input-file.csv> --forecast_point <forecast-point>')
        return 1
    data = open(filename, 'rb').read()
    data_size = sys.getsizeof(data)
    if data_size >= MAX_PREDICTION_FILE_SIZE_BYTES:
        print(
            'Input file is too large: {} bytes. '
            'Max allowed size is: {} bytes.'
        ).format(data_size, MAX_PREDICTION_FILE_SIZE_BYTES)
        return 1
    try:
        predictions = make_datarobot_deployment_predictions(data, deployment_id, forecast_point)
    except DataRobotPredictionError as exc:
        print(exc)
        return 1
    print(json.dumps(predictions))
    return 0
