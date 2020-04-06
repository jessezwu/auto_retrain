# auto_retrain

This repository is intended to be used as a starting template to setup a pipeline to automatically replace models.

The dataset used is sourced from the John Hopkins University COVID-19 repository [here](https://github.com/CSSEGISandData/COVID-19). A number of example timeseries models are built on each of the Australian states, and deployments are created for each. A text file is used to store the deployment ids and corresponding state (in reality this would likely be stored in a table or elsewhere).

On an ongoing basis, cron jobs are run to:

* make predictions for the next day
* pull the latest data, and upload as actuals to the respective deployments
* compare accuracy of models against actuals, and
    * retrain and redeploy if recent performance exceeds a threshold


## Installation

Prerequisites: python installed, DataRobot account, cron

Update your API token and install location
```
<editor of choice> drconfig.yaml
```

```
pip install -r requirements.txt
./data/pull_data.sh
```

## Running

For initial setup run
```
python create_initial_deployments.py
```


