import mechanize
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import dd


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

    # Separate 1m and 3m
    one_meter = df[df["Height"] == "1M"].reset_index(drop=True)
    three_meter = df[df["Height"] == "3M"].reset_index(drop=True)

    return one_meter, three_meter


def optimize_list(df):
    # TODO: optimize list for 6 and 11 dives
    dd_tables = dd.create_dd_tables()
    pass


if __name__ == "__main__":
    # name = input("Enter the diver's name: ")
    name = "Logan Sherwin"
    one_meter, three_meter = get_diver_data(name)

    # one_opt = optimize_list(one_meter)
    # three_opt = optimize_list(three_meter)
