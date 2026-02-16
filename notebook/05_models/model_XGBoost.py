import xgboost as xgb
import model_XGBoost as xgb_model

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil.relativedelta import relativedelta
import datetime as dt
import holidays
holidays_de= holidays.Germany()

from sklearn.metrics import mean_squared_error

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
                           max_depth=5)
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