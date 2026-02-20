from cgitb import enable

import xgboost as xgb

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
import datetime as dt
import holidays
holidays_de= holidays.Germany()

from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV, TimeSeriesSplit
import scipy.stats as stats

plt.rcParams['figure.figsize'] = [12, 6]
plt.rcParams['figure.dpi'] = 100

def create_and_train_XGBoost(train: pd.DataFrame, test: pd.DataFrame, FEATURES: list, TARGET: str) -> xgb.XGBRegressor:
    X_train = train[FEATURES]
    y_train = train[TARGET]

    X_test = test[FEATURES]
    y_test = test[TARGET]

    # n_estimators : number of trees being created
    reg = xgb.XGBRegressor(base_score=0.5,
                           n_estimators=1500,
                           learning_rate=0.01,
                           early_stopping_rounds=500,
                           objective='reg:squarederror',
                           colsample_bytree=0.8,
                           subsample=0.8,
                           max_depth=5,
                           enable_categorial=True)
    reg.fit(X_train, y_train,
            eval_set=[(X_train, y_train), (X_test, y_test)],
            verbose=50 # True prints always, number gives the n-th result
            )

    return reg

def display_feature_importance(reg: xgb.XGBRegressor) -> None:
    fi = pd.DataFrame(data=reg.feature_importances_,
                index=reg.feature_names_in_,
                columns=['importance']
                )
    fi.sort_values('importance').plot(kind='barh', title='Feature Importances')
    plt.show()

def paramater_search_XGBoost(train: pd.DataFrame, FEATURES: list, TARGET: str, search_kind: str, param_dist: dict) -> xgb.XGBRegressor:
    X_train = train[FEATURES]
    y_train = train[TARGET]

    # Create the XGBoost model object
    xgb_model = xgb.XGBRegressor()

    if search_kind == 'grid':
        best_model = grid_search_XGBoost(X_train, y_train, xgb_model, param_dist)
        return best_model
    elif search_kind == 'random':
        best_model = random_search_XGBoost(X_train, y_train, xgb_model, param_dist)
        return best_model






def grid_search_XGBoost(X_train: pd.DataFrame, y_train: pd.Series, xgb_model: xgb.XGBRegressor, param_dist: dict) -> xgb.XGBRegressor:
    # Create the GridSearchCV object
    grid_search = GridSearchCV(xgb_model, param_dist, scoring='neg_root_mean_squared_error', n_jobs=5) #cv=TimeSeriesSplit(n_splits=5)

    # Fit the GridSearchCV object to the training data
    grid_search.fit(X_train, y_train)

    # Print the best set of hyperparameters and the corresponding score
    print("Best set of hyperparameters: ", grid_search.best_params_)
    print("Best score: ", grid_search.best_score_)

    return grid_search.best_estimator_

def random_search_XGBoost(X_train: pd.DataFrame, y_train: pd.Series, xgb_model: xgb.XGBRegressor, param_dist: dict) -> xgb.XGBRegressor:
    # Create the RandomizedSearchCV object
    random_search = RandomizedSearchCV(xgb_model, param_distributions=param_dist, n_iter=20, cv=5, scoring='neg_root_mean_squared_error')

    # Fit the RandomizedSearchCV object to the training data
    random_search.fit(X_train, y_train)

    # Print the best set of hyperparameters and the corresponding score
    print("Best set of hyperparameters: ", random_search.best_params_)
    print("Best score: ", random_search.best_score_)

    return random_search.best_estimator_