import pandas
import pandas as pd
import numpy as np


def csv_read():
    df_new = pandas.read_csv("data.csv")
    print(df_new["Zeitstempel"])
    df_new["Zeitstempel"] = pd.to_datetime(df_new["Zeitstempel"], yearfirst=True, utc=True)
    print(df_new["Zeitstempel"])
    print(df_new.loc[df_new["Zeitstempel"] > "2023-01-01 00:00:00"])
    print(np.datetime64("2022-01-01 00:00:00", "ns"))


if __name__ == "__main__":
    csv_read()