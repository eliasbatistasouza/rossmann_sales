import json
import pickle

import pandas as pd
from fastapi import FastAPI, Request
from rossmann.Rossmann import Rossmann

# Loading model
model = pickle.load(
    open("/home/elias/Repos/rossmann_sales/models/xgb_rossmann.pkl", "rb")
)

# Initialize FastAPI
app = FastAPI()


@app.post("/rossmann/predict")
async def rossmann_predict(request: Request):
    request_body = await request.body()
    test_json = json.loads(request_body)

    if test_json:
        test_raw = pd.read_json(test_json)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
