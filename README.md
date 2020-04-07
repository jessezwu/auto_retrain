# auto_retrain

This repository is intended to be used as a starting template to setup a pipeline to automatically replace models.

The dataset used is sourced from the John Hopkins University COVID-19 repository [here](https://github.com/CSSEGISandData/COVID-19). A number of example timeseries models are built on each of the Australian states, and deployments are created for each. A text file is used to store the deployment ids and corresponding state (in reality this would likely be stored in a table or elsewhere).

This project was set up in April 2020, as daily case numbers were being updated. On an ongoing basis, cron jobs can be set up to:

* pull the latest data, and upload as actuals to the respective deployments
* compare accuracy of models against actuals, and
    * retrain and redeploy if recent performance exceeds a threshold
* make predictions for the next day


## Installation

Prerequisites: python installed, DataRobot account, cron

Update your API token and install location
```
<editor of choice> drconfig.yaml
```

```
pip install -r requirements.txt
```

## Running

For initial setup run
```
./run_data_extract.sh
cd py
python create_initial_deployments.py
```

Note that this creates a number of autopilot projects, and so will take some time to run - you can restrict the number of states to speed things up.

Add these lines to your user crontab
```
# refresh data every night at 20:00
0 20 * * * <full_path>/run_data_extract.sh
# update actuals for past predictions
5 20 * * * <full_path>/run_actuals_upload.sh
# update deployments if necessary
10 20 * * * <full_path>/run_accuracy_check.sh
# make predictions for tomorrow
0 21 * * * <full_path>/run_predictions.sh
```

These scripts all source your bash profile before running, to emulate your user environment. Change as necessary.
