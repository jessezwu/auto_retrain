"""
Help understand how often an accuracy threshold is exceeded on backtesting.

This is not a part of the main template flow, but may be useful to help
understand what thresholds for accuracy will correspond to expected retraining
frequencies desired by the business. E.g. you may not want to retrain a model
every day, but once a week is acceptable.

1. Define your own accuracy check (two RMSE examples below)
2. Score backtests
3. Run accuracy check on backtests
"""
import numpy as np
import pandas as pd
import datarobot as dr
import sklearn.metrics


def get_best_ts_model(project, metric):
    """
    Get the best timeseries model from a project
    """
    lb = [
        m for m in project.get_models() if m.metrics[metric]['crossValidation']
    ]
    lb.sort(key=lambda x: x.metrics[metric]['crossValidation'])
    best_model = dr.DatetimeModel.get(project.id, lb[0].id)
    return best_model


def get_model_backtesting(model):
    """
    Compute backtest predictions, or download existing results
    """
    try:
        job = model.request_training_predictions(
            dr.enums.DATA_SUBSET.ALL_BACKTESTS)
        return job.get_result_when_complete().get_all_as_dataframe()
    except:
        predictions = [
            p for p in dr.TrainingPredictions.list(project.id)
            if p.model_id == model.id
        ][0]
        return predictions.get_all_as_dataframe()


def accuracy_check(backtests, actual_name, baseline):
    """
    Look at accuracy on a day by day basis (for all forecast windows)
    """
    def get_rmse(group):
        rmse = np.sqrt(
            sklearn.metrics.mean_squared_error(group[actual_name],
                                               group['prediction']))
        return pd.Series({'RMSE': rmse})

    df = joined.groupby('forecast_point').apply(get_rmse).reset_index()
    return df.assign(Failed=lambda x: x['RMSE'] > baseline)


def accuracy_check_n(backtests, actual_name, baseline, n):
    """
    Look at accuracy over last n days - to reduce noise
    """
    def get_rmse(group):
        rmse = np.sqrt(
            sklearn.metrics.mean_squared_error(group[actual_name],
                                               group['prediction']))
        return pd.Series({'RMSE': rmse})

    result = pd.DataFrame()
    dates = backtests['forecast_point'].sort_values().unique()
    for i in range(len(dates) - n):
        group = backtests[backtests['forecast_point'].between(
            dates[i], dates[i + n - 1])]
        result = result.append(
            pd.DataFrame({
                'RMSE': get_rmse(group),
                'forecast_point': group.forecast_point.max()
            }))
    return result.assign(Failed=lambda x: x['RMSE'] > baseline)


################################################################################
# testing, intended for interactive use
################################################################################

# load actuals, and project (replace id)
data = pd.read_csv('../data/australian_cases.csv')
data = data[data['Province/State'] == 'New South Wales'] \
        .assign(timestamp = lambda x: pd.to_datetime(x['date'], utc=True))
project = dr.Project.get('id')
metric = 'RMSE'
# compute backtest predictions
model = get_best_ts_model(project, metric)
backtesting = get_model_backtesting(model)
# join with actuals
actuals = data[['cases', 'timestamp']]
backtesting = backtesting.assign(
    timestamp=lambda x: pd.to_datetime(x['timestamp']))
joined = pd.merge(backtesting, actuals)
baseline = model.metrics[metric]['backtesting']
# inspect effect of different checking methods
accuracy_check(joined, 'cases', baseline)
accuracy_check_n(joined, 'cases', baseline, 3)
accuracy_check_n(joined, 'cases', baseline * 1.2, 3)
