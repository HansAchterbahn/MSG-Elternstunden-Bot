from tabulate import tabulate
import pandas as pd
from csv_diff import load_csv, compare

def tab(dataframe):
    print(tabulate(dataframe, headers='keys', tablefmt='github'))
    print("")

def csv_diff_pandas():
    df_new = pd.read_csv('data.csv', index_col=0)
    df_old = pd.read_csv('data.old.csv', index_col=0)

    tab(df_new)
    tab(df_old)

    comparison_df = pd.merge(df_old, df_new, indicator=True, how="right")
    tab(comparison_df)

    diff_df = comparison_df[comparison_df["_merge"] != "both"]
    tab(diff_df)

    tab(df_old.drop(df_new.index))

# Use csv-diff
# - looks quite òk -> easy to use and straight forward
def csv_diff_csv_diff():
    file_new = load_csv(open("data.csv"))
    file_old = load_csv(open("data.old.csv"))

    print(file_old)

    difference = compare(file_old,file_new)
    print(difference['added'][0]['Arbeitskreis'])

if __name__ == "__main__":
    #csv_diff_pandas()
    csv_diff_csv_diff()