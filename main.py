import csv
import json
import pandas
import pandas as pd
import datetime
import numpy as np
from tabulate import tabulate

def tab(dataframe):
    print(tabulate(dataframe, headers='keys', tablefmt='github'))
    print("")

# Use csv-diff
# - looks quite òk -> easy to use and straight forward
def csv_read():
    with open("data.csv", newline="") as csv_file_handler:
        csv_file = csv.reader(csv_file_handler)
        for row in csv_file:
            print('\t '.join(row))

def csv_read_pandas():
    df_new = pandas.read_csv("data.csv")
    print(df_new["Zeitstempel"])
    df_new["Zeitstempel"] = pd.to_datetime(df_new["Zeitstempel"], yearfirst=True, utc=True)
    print(df_new["Zeitstempel"])
    #df_new.query(df_new["Zeitstempel"] > np.datetime64("2022-01-01 00:00:00", "ns"))
    print(np.datetime64("2022-01-01 00:00:00", "ns"))

def json_read():
    with open("data.json") as new_data_file:
        new_data = json.load(new_data_file)

        print(json.dumps(new_data, sort_keys=True, indent=2))

if __name__ == "__main__":
    #csv_read()
    #json_read()
    csv_read_pandas()