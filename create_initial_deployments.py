import datarobot as dr
import pandas as pd
import drutils as du

# setup
dataset = 'data/australian_cases.csv'
timecol = 'date'
target = 'cases'
series = 'Province/State'
metric = 'MAE'
ref_file = 'reference.csv'

# series
states = ['New South Wales', 'Victoria', 'Queensland', 'South Australia']

df = pd.read_csv(dataset)
df = df[df[series].isin(states)]

dr.Client(config_path='drconfig.yaml')

################################################################################
# project setup

spec = dr.DatetimePartitioningSpecification(timecol,
                                            use_time_series=True,
                                            default_to_known_in_advance=False)
# disable holdout
spec.disable_holdout = True
# backtest options
spec.number_of_backtests = 2
spec.validation_duration = dr.partitioning_methods.construct_duration_string(
    days=7)
# windows
spec.feature_derivation_window_start = -14
spec.feature_derivation_window_end = 0
spec.forecast_window_start = 1
spec.forecast_window_end = 3

################################################################################

# list currently built projects - don't retrain if project already exists
built_projects = dr.Project.list()
built_names = [p.project_name for p in built_projects]
# same list for deployments
deployments = dr.Deployment.list()
deployment_names = [d.label for d in deployments]

# pull out server information for deployment
prediction_server = dr.PredictionServer.list()[0]

reference = pd.DataFrame()

# iterate through series
for s in df[series].unique():
    proj_name = 'auto retrain ' + s + ' ' + df[timecol].max()
    subdf = df[df[series] == s]
    print('creating deployment for ' + s)
    # get or create project
    if proj_name in built_names:
        # take existing project
        project = built_projects[built_names.index(proj_name)]
    else:
        # upload data and create project
        project = dr.Project.create(subdf, project_name=proj_name)
        # finalise project, and run autopilot with max workers
        project.set_target(target,
                           partitioning_method=spec,
                           metric=metric,
                           worker_count=-1)
        project.wait_for_autopilot()
    # take best model and deploy
    model = dr.ModelRecommendation.get(project.id).get_model()
    if proj_name in deployment_names:
        deployment = deployments[deployment_names.index(proj_name)]
    else:
        deployment = dr.Deployment.create_from_learning_model(
            model.id,
            label=proj_name,
            description='Australian coronavirus cases',
            default_prediction_server_id=prediction_server.id)
    # ensure deployment settings are turned on
    deployment.update_drift_tracking_settings(target_drift_enabled=True, feature_drift_enabled=True, max_wait=60)
    deployment.update_association_id_settings(column_names=['id'], required_in_prediction_requests=True, max_wait=60)
    # get metric for parent of frozen model
    parent = du.get_parent_model(model)
    # store information for later use
    reference = reference.append(
        pd.DataFrame([{
            'use_case': s,
            'latest_project': project.id,
            'deployment_id': deployment.id,
            'error': parent.metrics['MAE']['crossValidation']
        }]))

reference.to_csv(ref_file)
