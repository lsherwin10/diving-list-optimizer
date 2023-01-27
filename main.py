import re

import mechanize
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

import dd

# Gets data from divemeets.com and returns 1m and 3m dive results
def get_diver_data(name):
    br = mechanize.Browser()

    # Split name
    comps = name.split()
    if len(comps) != 2:
        raise Exception("Name provided must be two words (First Last)")
    first, last = comps

    # Submit member search form
    url = "https://secure.meetcontrol.com/divemeets/system/memberlist.php"
    br.open(url)
    br.select_form(nr=0)
    br.form["first"] = first
    br.form["last"] = last
    req = br.submit()
    soup = BeautifulSoup(req.read(), "html.parser")
    br.close()

    # Get diver link
    link = soup.find("a", attrs={"href": re.compile("profile.php")}).get("href")
    url = url[: url.rindex("/") + 1]
    diver_link = url + link

    # Get table data from DiveMeets statistics
    return get_diver_stats(diver_link)


# Parses the Dive Statistics table to get 1m and 3m lists
def get_diver_stats(url):
    diver_req = requests.get(url)
    df = pd.read_html(diver_req.text, flavor="html5lib")[-1]

    # Remove extra rows and columns
    df.dropna(inplace=True)
    df.columns = df.iloc[1]
    df.drop([0, 1], inplace=True)
    df.drop(columns=["Description", "High Score", "# of Times"], inplace=True)

    # Rename Dive and Height cols
    cols = df.columns.values
    cols[0] = "Dive"
    cols[1] = "Height"
    df.columns = cols

    # Add Position col and rearrange
    df["Position"] = df["Dive"].str[-1]
    df["Dive"] = df["Dive"].str[:-1]

    cols = df.columns.values[:-1]
    cols = np.insert(cols, 1, "Position")
    df = df[cols]

    df.reset_index(drop=True, inplace=True)
    df["Avg Score"] = df["Avg Score"].astype(float)

    # Separate 1m and 3m
    one_meter = df[df["Height"] == "1M"].reset_index(drop=True)
    three_meter = df[df["Height"] == "3M"].reset_index(drop=True)

    return one_meter, three_meter


# Takes in dives for a specific board and chooses the optimal list
def optimize_list(df, height, champ=False):
    # dd_tables = dd.create_dd_tables()

    # Optimize for 11-dive list
    if champ:
        dd_vol_max = 0.0
        if height == "1M":
            dd_vol_max = 9.0
        elif height == "3M":
            dd_vol_max = 9.5
        else:
            raise Exception("Illegal height parameter specified")

    # TODO: Optimize voluntaries using DDs

    # Optimize for 6-dive list
    else:
        idx = []
        remove_idx = []
        for cat in range(1, 6):
            cat_dives = df[df["Dive"].str.startswith(str(cat))]
            dive_idx = cat_dives["Avg Score"].idxmax()
            idx.append(dive_idx)
            dive_num = df.iloc[dive_idx, 0]
            remove_idx += list(
                cat_dives.loc[cat_dives["Dive"] == dive_num].index.values
            )

        rem_dives = df.loc[~df.index.isin(remove_idx)]
        idx.append(rem_dives["Avg Score"].idxmax())

        return df.loc[idx].reset_index(drop=True)


def run(name):
    one_meter, three_meter = get_diver_data(name)

    one_opt = optimize_list(one_meter, "1M")
    three_opt = optimize_list(three_meter, "3M")

    print(one_opt)
    print(f"1M Total: {one_opt['Avg Score'].sum():.2f}")
    print()
    print(three_opt)
    print(f"3M Total: {three_opt['Avg Score'].sum():.2f}")


if __name__ == "__main__":
    name = input("Enter the diver's name: ")
    run(name)
