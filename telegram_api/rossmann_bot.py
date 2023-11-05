import json

import pandas as pd
import requests
from flask import Flask, Response, request

# Bot token
TOKEN = "6987629551:AAGrX5xJynwfGr30SVROrTA2vZ_Z1-1LPwo"

"""
# Bot Info
https://api.telegram.org/bot6987629551:AAGrX5xJynwfGr30SVROrTA2vZ_Z1-1LPwo/getMe

# getUpdates
https://api.telegram.org/bot6987629551:AAGrX5xJynwfGr30SVROrTA2vZ_Z1-1LPwo/getUpdates

# sendMessage
https://api.telegram.org/bot6987629551:AAGrX5xJynwfGr30SVROrTA2vZ_Z1-1LPwo/sendMessage?chat_id=100307589&text=testback

# setWebhook
https://api.telegram.org/bot6987629551:AAGrX5xJynwfGr30SVROrTA2vZ_Z1-1LPwo/setWebhook?url=https://125804b2fee547.lhr.life
"""


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&parse_mode=html"

    r = requests.post(url, json={"text": text})
    print("Status Code {r.status_code}")

    return None


def load_dataset(store_id):
    # loading test dataset
    df10 = pd.read_csv("../data/raw/test.csv")
    df_store_raw = pd.read_csv("../data/raw/store.csv")
    # Merge testa and store dataset
    df_test = pd.merge(df10, df_store_raw, how="left", on="Store")

    # Choose store for prediction
    df_test = df_test[df_test["Store"] == store_id]

    if not df_test.empty:
        # Remove closed days
        df_test = df_test[df_test["Open"] != 0]
        df_test = df_test[~df_test["Open"].isnull()]

        # Remove Id
        df_test = df_test.drop("Id", axis=1)

        # Convert dataframe to json
        data = json.dumps(df_test.to_dict(orient="records"))

    else:
        data = "error"

    return data


def predict(data):
    # API call
    url = "https://rossmann-6xtx.onrender.com/rossmann/predict"
    header = {"Content-type": "application/json"}

    r = requests.post(url, data=data, headers=header)
    print(f"Status Code {r.status_code}")
    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1


def parse_message(message):
    chat_id = message["message"]["chat"]["id"]
    command = message["message"]["text"]

    store_id = command.replace("/", "")

    try:
        store_id = int(store_id)

    except ValueError:
        store_id = "error"

    return chat_id, store_id, command


# API initialize
app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method:
        message = request.get_json()

        chat_id, store_id, command = parse_message(message)

        if command == "/start":
            msg = "<b>Welcome to Rossmann Sales Prediction Bot</b>\n\nThis bot uses machine learning model to simulate prediction for Rossmann Store sales in the next six weeks.\n\nType /help to see available commands.\n\n<b>Author:</b> @eliasbatista | www.eliasbatista.com\n\n<b>Note: First prediction might take a while.</b>"
            send_message(chat_id, msg)
            return Response("Ok", status=200)

        elif command == "/help":
            msg = "<b>Available commands:</b>\n\n/about to know iformation about this project\n/help to see available commands\n/prediction to receive prediction instrunctions"
            send_message(chat_id, msg)
            return Response("Ok", status=200)

        elif command == "/about":
            msg = "<b>About this project:</b>\n\nThis bot was developed as a machine learning portifolio project, it uses public data and a XGBoost Regressor Model to predict Rossmann Store sales for the next six weeks.\n\nVisit the project github page at: eliasbatista.com/rossmann_sales\n\nTo get in touch with the author:\nTelegram: @eliasbatista\nPortfolio: www.eliasbatista.com"
            send_message(chat_id, msg)
            return Response("Ok", status=200)

        elif command == "/prediction":
            msg = "To make sales prediction type /42 (you can change 42 for any valid Store ID)"
            send_message(chat_id, msg)
            return Response("Ok", status=200)

        elif store_id == "error":
            msg = "Not a valid command, /help to see a list of available commands."
            send_message(chat_id, msg)
            return Response("Ok", status=200)

        else:
            # load data
            data = load_dataset(store_id)

            if data != "error":
                # predict
                d1 = predict(data)
                d2 = (
                    d1.loc[:, ["store", "prediction"]]
                    .groupby("store")
                    .sum()
                    .reset_index()
                )

                store = d2["store"].values[0]
                prediction = d2["prediction"].values[0]

                msg = f"Store <b>{store}</b> will sell <b>$ {prediction:,.2f}</b> in the next six weeks."

                send_message(chat_id, msg)
                return Response("Ok", status=200)

            else:
                msg = "Store ID not valid."
                send_message(chat_id, msg)
                return Response("Ok", status=200)

    else:
        return "<b>Rossmann Sales Prediction Bot</b>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
