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

from sklearn.metrics import mean_squared_error
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
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

def paramater_search_XGBoost(train: pd.DataFrame, FEATURES: list, TARGET: str, search_kind: str, param_dist: dict) -> None:
    X_train = train[FEATURES]
    y_train = train[TARGET]

    # Create the XGBoost model object
    xgb_model = xgb.XGBClassifier()

    if search_kind == 'grid':
        grid_search_XGBoost(X_train, y_train, xgb_model, param_dist)
    elif search_kind == 'random':
        random_search_XGBoost(X_train, y_train, xgb_model, param_dist)


def grid_search_XGBoost(X_train: pd.DataFrame, y_train: pd.Series, xgb_model: xgb.XGBClassifier, param_dist: dict) -> None:
    # Create the GridSearchCV object
    grid_search = GridSearchCV(xgb_model, param_dist, cv=5, scoring='accuracy')

    # Fit the GridSearchCV object to the training data
    grid_search.fit(X_train, y_train)

    # Print the best set of hyperparameters and the corresponding score
    print("Best set of hyperparameters: ", grid_search.best_params_)
    print("Best score: ", grid_search.best_score_)

def random_search_XGBoost(X_train: pd.DataFrame, y_train: pd.Series, xgb_model: xgb.XGBClassifier, param_dist: dict) -> None:
    # Create the RandomizedSearchCV object
    random_search = RandomizedSearchCV(xgb_model, param_distributions=param_dist, n_iter=10, cv=5, scoring='accuracy')

    # Fit the RandomizedSearchCV object to the training data
    random_search.fit(X_train, y_train)

    # Print the best set of hyperparameters and the corresponding score
    print("Best set of hyperparameters: ", random_search.best_params_)
    print("Best score: ", random_search.best_score_)