import pickle

import pandas as pd
from flask import Flask, Response, request
from rossmann.Rossmann import Rossmann

# loading model
model = pickle.load(
    open("/home/elias/Repos/rossman_sales/models/xgb_rossman.pkl", "rb")
)

# Initialize API
app = Flask(__name__)


@app.route("/rossmann/predict", methods=["POST"])
def rossmann_predict():
    test_json = request.get_json()

    if test_json:
        if isinstance(test_json, dict):
            test_raw = pd.DataFrame(test_json, index=[0])
        else:
            test_raw = pd.DataFrame(test_json, columns=test_json[0].keys())

        # Instantiate Rossmann class
        pipeline = Rossmann()

        # Data cleaning
        df1 = pipeline.data_cleaning(test_raw)
        # feature engineering
        df2 = pipeline.feature_eng(df1)
        # data preparation
        df3 = pipeline.data_preparation(df2)
        # prediction
        df_response = pipeline.get_prediction(model, test_raw, df3)

        return df_response

    else:
        return Response("{}", status=200, mimetype="application/json")


if __name__ == "__main__":
    app.run("0.0.0.0")