import datetime
import math
import pickle

import inflection
import numpy as np
import pandas as pd


class Rossmann(object):
    def __init__(self):
        self.home_path = "/home/elias/Repos/rossman_sales"
        self.competition_distance_scaler = pickle.load(
            open(self.home_path + "/parameters/competition_distance_scaler.pkl", "rb")
        )
        self.competition_time_month_scaler = pickle.load(
            open(self.home_path + "/parameters/competition_time_month_scaler.pkl", "rb")
        )
        self.promo_time_week_scaler = pickle.load(
            open(self.home_path + "/parameters/promo_time_week_scaler.pkl", "rb")
        )
        self.year_scaler = pickle.load(
            open(self.home_path + "/parameters/year_scaler.pkl", "rb")
        )
        self.store_type_scaler = pickle.load(
            open(self.home_path + "/parameters/store_type_scaler.pkl", "rb")
        )

    def data_cleaning(self, dataframe):
        # Rename columns
        cols_old = list(dataframe)
        # Function from rename
        snakecase = lambda x: inflection.underscore(x)
        cols_new = list(map(snakecase, cols_old))
        # Renaming columns
        dataframe.columns = cols_new

        # Fix date type
        dataframe["date"] = pd.to_datetime(dataframe["date"])

        # Fillout Na's
        dataframe["competition_distance"] = dataframe["competition_distance"].apply(
            lambda x: 200000.0 if math.isnan(x) else x
        )
        # competition_open_since_month
        dataframe["competition_open_since_month"] = dataframe.apply(
            lambda x: x["date"].month
            if math.isnan(x["competition_open_since_month"])
            else x["competition_open_since_month"],
            axis=1,
        )
        # competition_open_since_year
        dataframe["competition_open_since_year"] = dataframe.apply(
            lambda x: x["date"].year
            if math.isnan(x["competition_open_since_year"])
            else x["competition_open_since_year"],
            axis=1,
        )
        # promo2_since_week
        dataframe["promo2_since_week"] = dataframe.apply(
            lambda x: x["date"].week
            if math.isnan(x["promo2_since_week"])
            else x["promo2_since_week"],
            axis=1,
        )
        # promo2_since_year
        dataframe["promo2_since_year"] = dataframe.apply(
            lambda x: x["date"].year
            if math.isnan(x["promo2_since_year"])
            else x["promo2_since_year"],
            axis=1,
        )
        # promo_interval
        month_map = {
            1: "Jan",
            2: "Fev",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }
        dataframe["promo_interval"].fillna(0, inplace=True)
        dataframe["month_map"] = dataframe["date"].dt.month.map(month_map)
        dataframe["is_promo"] = dataframe[["promo_interval", "month_map"]].apply(
            lambda x: 0
            if x["promo_interval"] == 0
            else 1
            if x["month_map"] in x["promo_interval"].split(",")
            else 0,
            axis=1,
        )

        dataframe["competition_open_since_month"] = dataframe[
            "competition_open_since_month"
        ].astype(int)
        dataframe["competition_open_since_year"] = dataframe[
            "competition_open_since_year"
        ].astype(int)
        dataframe["promo2_since_week"] = dataframe["promo2_since_week"].astype(int)
        dataframe["promo2_since_year"] = dataframe["promo2_since_year"].astype(int)

        return dataframe

    def feature_eng(self, dataframe):
        # Creating datetimes
        # Year
        dataframe["year"] = dataframe["date"].dt.year

        # Month
        dataframe["month"] = dataframe["date"].dt.month

        # Day
        dataframe["day"] = dataframe["date"].dt.day

        # Week of Year
        dataframe["week_of_year"] = dataframe["date"].dt.isocalendar().week

        # Year Week
        dataframe["year_week"] = dataframe["date"].dt.strftime("%Y-%W")

        dataframe["competition_since"] = dataframe.apply(
            lambda x: datetime.datetime(
                year=x["competition_open_since_year"],
                month=x["competition_open_since_month"],
                day=1,
            ),
            axis=1,
        )
        dataframe["competition_time_month"] = (
            ((dataframe["date"] - dataframe["competition_since"]) / 30)
            .apply(lambda x: x.days)
            .astype(int)
        )

        # Promo Since
        dataframe["promo_since"] = (
            dataframe["promo2_since_year"].astype(str)
            + "-"
            + dataframe["promo2_since_week"].astype(str)
        )
        dataframe["promo_since"] = dataframe["promo_since"].apply(
            lambda x: datetime.datetime.strptime(x + "-1", "%Y-%W-%w")
            - datetime.timedelta(days=7)
        )
        dataframe["promo_time_week"] = (
            ((dataframe["date"] - dataframe["promo_since"]) / 7)
            .apply(lambda x: x.days)
            .astype(int)
        )

        # Assortment
        dataframe["assortment"] = dataframe["assortment"].apply(
            lambda x: "basic" if x == "a" else "extra" if x == "b" else "extended"
        )

        # State Holiday
        dataframe["state_holiday"] = dataframe["state_holiday"].apply(
            lambda x: "public_holiday"
            if x == "a"
            else "easter_holiday"
            if x == "b"
            else "christmas"
            if x == "c"
            else "regular_day"
        )

        # Filter lines
        dataframe = dataframe.loc[(dataframe["open"] != 0), :]

        # Filter columns
        dataframe = dataframe.drop(["open", "promo_interval", "month_map"], axis=1)

        return dataframe

    def data_preparation(self, dataframe):
        # Rescaling

        # competition distance
        dataframe[
            "competition_distance"
        ] = self.competition_distance_scaler.fit_transform(
            dataframe[["competition_distance"]].values
        )

        # competition time month
        dataframe[
            "competition_time_month"
        ] = self.competition_time_month_scaler.fit_transform(
            dataframe[["competition_time_month"]].values
        )

        # promo time week
        dataframe["promo_time_week"] = self.promo_time_week_scaler.fit_transform(
            dataframe[["promo_time_week"]].values
        )

        # year
        dataframe["year"] = self.year_scaler.fit_transform(dataframe[["year"]].values)

        # Encoding
        # state holiday - One Hot Encoding
        dataframe = pd.get_dummies(
            dataframe, prefix=["state_holiday"], columns=["state_holiday"]
        )

        # store type - Label Encoder
        dataframe["store_type"] = self.store_type_scaler.fit_transform(
            dataframe["store_type"]
        )

        # assortment
        assortment_dict = {
            "basic": 1,
            "extra": 2,
            "extended": 3,
        }

        dataframe["assortment"] = dataframe["assortment"].map(assortment_dict)

        # Natural Transformation
        # month
        dataframe["month_sin"] = dataframe["month"].apply(
            lambda x: np.sin(x * (2.0 * np.pi / 12))
        )
        dataframe["month_cos"] = dataframe["month"].apply(
            lambda x: np.cos(x * (2.0 * np.pi / 12))
        )

        # day
        dataframe["day_sin"] = dataframe["day"].apply(
            lambda x: np.sin(x * (2.0 * np.pi / 30))
        )
        dataframe["day_cos"] = dataframe["day"].apply(
            lambda x: np.cos(x * (2.0 * np.pi / 30))
        )

        # day of week
        dataframe["day_of_week_sin"] = dataframe["day_of_week"].apply(
            lambda x: np.sin(x * (2.0 * np.pi / 7))
        )
        dataframe["day_of_week_cos"] = dataframe["day_of_week"].apply(
            lambda x: np.cos(x * (2.0 * np.pi / 7))
        )

        # week of year
        dataframe["week_of_year_sin"] = dataframe["week_of_year"].apply(
            lambda x: np.sin(x * (2.0 * np.pi / 52))
        )
        dataframe["week_of_year_cos"] = dataframe["week_of_year"].apply(
            lambda x: np.cos(x * (2.0 * np.pi / 52))
        )

        dataframe = dataframe.drop(
            [
                "day_of_week",
                "day",
                "month",
                "week_of_year",
                "promo_since",
                "competition_since",
                "year_week",
            ],
            axis=1,
        )

        cols_selected = [
            "store",
            "promo",
            "store_type",
            "assortment",
            "competition_distance",
            "competition_open_since_month",
            "competition_open_since_year",
            "promo2",
            "promo2_since_week",
            "promo2_since_year",
            "competition_time_month",
            "promo_time_week",
            "month_sin",
            "month_cos",
            "day_sin",
            "day_cos",
            "day_of_week_sin",
            "day_of_week_cos",
            "week_of_year_sin",
            "week_of_year_cos",
        ]

        dataframe = dataframe.loc[:, cols_selected]

        return dataframe

    def get_prediction(self, model, original_data, test_data):
        # prediction
        pred = model.predict(test_data)

        # join pred into the original data
        original_data["prediction"] = np.expm1(pred)

        return original_data.to_json(orient="records", date_format="iso")
