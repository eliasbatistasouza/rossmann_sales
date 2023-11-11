import json
import os

import pandas as pd
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Bot token
TOKEN = os.environ.get("TOKEN")

app = FastAPI()


def parse_message(text):
    # Check if the message is a command
    if text[0] == "/":
        # Remove the leading slash and split the command
        command = text.replace("/", "")
        try:
            store_id = int(command)

        except ValueError:
            store_id = "error"

    else:
        command = "error"
        store_id = "error"

    return store_id, command


def handle_command(chat_id, command):
    """
    Function to handle Telegram commands.
    """

    # Check the command and perform the corresponding action
    if command == "start":
        msg = "<b>Welcome to Rossmann Sales Prediction Bot</b>\n\nThis bot uses machine learning model to simulate prediction for Rossmann Store sales in the next six weeks.\n\nType /help to see available commands.\n\n<b>Author:</b> @eliasbatista | www.eliasbatista.com\n\n<b>Note: First prediction might take a while.</b>"

        send_message(chat_id, msg)

    elif command == "help":
        msg = "<b>Available commands:</b>\n\n/about to know iformation about this project\n/help to see available commands\n/prediction to receive prediction instrunctions"

        send_message(chat_id, msg)

    elif command == "about":
        msg = "<b>About this project:</b>\n\nThis bot was developed as a machine learning portifolio project, it uses public data and a XGBoost Regressor Model to predict Rossmann Store sales for the next six weeks.\n\nVisit the project github page at: eliasbatista.com/rossmann_sales\n\nTo get in touch with the author:\nTelegram: @eliasbatista\nPortfolio: www.eliasbatista.com"

        send_message(chat_id, msg)

    elif command == "prediction":
        msg = "To make sales prediction type /42 (you can change 42 for any valid Store ID)"
        send_message(chat_id, msg)

    else:
        msg = "Not a valid command, /help to see a list of available commands."
        send_message(chat_id, msg)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=html"

    response = requests.post(url, params={"text": text})
    print(f"Status Code {response.status_code}")

    return JSONResponse(content={"message": "Ok"}, status_code=200)


def load_dataset(chat_id, store_id):
    # loading test dataset
    test = pd.read_csv("../data/raw/test.csv")
    store = pd.read_csv("../data/raw/store.csv")
    # Merge testa and store dataset
    dataframe = pd.merge(test, store, how="left", on="Store")

    # Choose store for prediction
    dataframe = dataframe.loc[dataframe["Store"] == store_id, :]

    if not dataframe.empty:
        # Remove closed days
        dataframe = dataframe[dataframe["Open"] != 0]
        dataframe = dataframe[~dataframe["Open"].isnull()]

        # Remove Id
        dataframe = dataframe.drop("Id", axis=1)

        # Convert dataframe to json
        data = dataframe.to_json(orient="records")

    else:
        data = "error"
        msg = "Store ID not valid."
        send_message(chat_id, msg)

    return data


def predict(data):
    # API call
    url = "https://rossmann-6xtx.onrender.com/rossmann/predict"

    response = requests.post(url, json=data)
    print(f"Status Code {response.status_code}")
    prediction = json.loads(response.json())

    return prediction


def pred_message(chat_id, prediction):
    prediction = pd.DataFrame(prediction)
    prediction = (
        prediction.loc[:, ["store", "prediction"]].groupby("store").sum().reset_index()
    )

    store = prediction["store"].values[0]
    value = prediction["prediction"].values[0]

    msg = f"Store <b>{store}</b> will sell <b>€ {value:,.2f}</b> in the next six weeks."
    send_message(chat_id, msg)

    return None


@app.post("/")
async def index(request: Request):
    request_body = await request.body()
    message = json.loads(request_body)

    chat_id = message["message"]["chat"]["id"]
    text = message["message"]["text"]

    store_id, command = parse_message(text)

    if store_id != "error":
        data = load_dataset(chat_id, store_id)
        if data != "error":
            prediction = predict(data)
            pred_message(chat_id, prediction)

    else:
        handle_command(chat_id, command)


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI application with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
