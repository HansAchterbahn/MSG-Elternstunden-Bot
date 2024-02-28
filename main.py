import pandas as pd
import tomli


last_timestamp = "2023-01-01 00:00:00"
def csv_read(file_path):
    df_new = pd.read_csv(file_path)        # read csv file to dataframe
    df_new["Zeitstempel"] = (
        pd.to_datetime(df_new["Zeitstempel"], yearfirst=True, utc=True)) # convert timestamp strings to UTC+0 values
    print(df_new["Zeitstempel"])
    print(df_new.loc[df_new["Zeitstempel"] > last_timestamp])

if __name__ == "__main__":
    with open("config.toml", "rb") as f:
        toml_dict = tomli.load(f)
        
    csv_read("data.csv")