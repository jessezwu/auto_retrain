import datarobot as dr
import pandas as pd
import drutils as du
import yaml

# setup
dataset = 'data/australian_cases.csv'
ref_file = 'reference.csv'
out_file = 'data/scores.csv'

timecol = 'date'
target = 'cases'
series = 'Province/State'
history = 28
horizon = 3

with open('drconfig.yaml', 'r') as of:
    config = yaml.load(of, Loader=yaml.BaseLoader)

################################################################################

# credentials
token = config['token']
url, pred_key = du.get_default_pred_server_info()

# dataframes
df = pd.read_csv(dataset)
reference = pd.read_csv(ref_file)
try:
    output = pd.read_csv(out_file).drop_duplicates()
except:
    output = pd.DataFrame()

for idx, row in reference.iterrows():
    # generate prediction dataset with association id
    pred_data = df[df[series] == row['use_case']] \
            .sort_values(timecol) \
            .tail(history)
    predict_date = max(pred_data[timecol])
    pred_data = pred_data.append(
            pd.DataFrame({
                timecol: pd.date_range(predict_date, periods=horizon+1, freq='D', closed='right').strftime('%Y-%m-%d'),
                series: row['use_case']
            }), sort=False) \
            .assign(id = lambda x: x[series] + ' ' + x[timecol])
    # call deployment
    response = du.make_timeseries_prediction(pred_data.to_csv(index=False),
                                             url, row['deployment_id'], token,
                                             pred_key)
    # parse json
    preds = du.parse_dr_predictions(response, timeseries=True) \
            .assign(series = row['use_case'])
    output = output.append(preds)

output.drop_duplicates().to_csv(out_file, index=False)
